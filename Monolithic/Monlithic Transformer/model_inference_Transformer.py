from time import sleep
from kafka import KafkaProducer, KafkaConsumer
import json
from json import dumps
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from Feature_extractor_T import ProcessData
import paho.mqtt.client as mqtt
from collections import deque
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import pickle
import queue
from collections import deque

token = "HPskNZN757ImNKb7CmOtEpfX4y2wD_2jiLNZ_TdXYMyBBUqkFBKMa26rCXaCpNuia-MbW7nSrhe9-DdFzQ_VvA=="
org = "iff"
url = "http://192.168.50.202:8086"
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

fs = 2148
FS = 2148
window_size = 30
window_shift = 18
feature_list = ['RMS', 'MAV', 'WL', 'ZC', 'MDF', 'MNF', 'MNP', 'SSC']  # List of required features
feature_columns = ['RMS', 'MAV', 'WL', 'SSC', 'MDF', 'MNF', 'MNP', 'PSD', 'stft_feature_1', 'stft_feature_2', 'stft_feature_3']



MODEL_path = "E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/Transformer.h5"
model = load_model(MODEL_path)
# Load the scaler from the file
with open('E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/scalerT.pkl', 'rb') as file:
    loaded_scaler = pickle.load(file)
print("Scaler has been loaded from 'scaler.pkl'")

###################################################################################################################################

producer = KafkaProducer(bootstrap_servers=['192.168.50.234:29093'],
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'))

# Set up Kafka consumer
consumer = KafkaConsumer(
    'delsys-source-emg01',                  # Specify the topic name
    bootstrap_servers='192.168.50.234:29093', # Specify the Kafka broker(s)
    group_id='91', # Specify the consumer group ID
    auto_offset_reset='latest',       # Set the offset to the beginning of the topic
    enable_auto_commit=True,            # Enable auto commit offsets
    auto_commit_interval_ms=1000,       # Set auto commit interval (in milliseconds)
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  
    )   

# Queues for inter-thread communication
message_queue = queue.Queue()
processed_data_queue = queue.Queue()
time_steps = 300


request_counter = 0
throughput_window = deque(maxlen=60)  # 60 seconds window

import psutil

def get_cpu_memory_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    memory_usage_mb = memory_usage / (1024 ** 2)  # Convert bytes to MB
    return cpu_usage, memory_usage_mb

def get_disk_io():
    disk_io = psutil.disk_io_counters()
    return disk_io.read_bytes, disk_io.write_bytes

def calculate_throughput():
    return sum(throughput_window) / len(throughput_window)

def infer(input_data):
    start_time = time.time()
    prediction = model.predict(input_data)
    predicted_class = np.argmax(prediction, axis=-1)
    result = np.ndarray.item(predicted_class)
    end_time = time.time()
     # Print or handle the prediction
    print(f'Predicted Class: {predicted_class[0]}')
    latency = end_time-start_time

    return result,latency


def process_data():
    df_ary = pd.DataFrame()
    global request_counter
    while True:
        for message in consumer:
            start_time = time.time()
            request_counter += 1
            data = message.value
            df = pd.DataFrame(data)

            processed = process_data1(df,FS,fs,window_size,window_shift,feature_list)
            X1=processed[feature_columns]
            #print(X1)

            df_json_str = processed.to_json(orient="records")
            df_json_obj = json.loads(df_json_str)

            producer.send("EMG_Features_Monolithic", value=df_json_obj )
            save_to_influx_FE("Monolithic_Transformer", processed)

            # Append new data to df_ary
            df_ary = pd.concat([df_ary, X1], ignore_index=True)

            if len(df_ary)>=300:

                X2 = df_ary.iloc[:300]

                X_scaled = loaded_scaler.transform(X2)

                sequence =  X_scaled.reshape((1,300,11))

                result,Infer_latency = infer(sequence)

                

                cpu_usage, memory_usage = get_cpu_memory_usage()
                read_bytes, write_bytes = get_disk_io()
                throughput_window.append(request_counter)

                throughtput = calculate_throughput()
                requect_latency = time.time() -start_time
                save_to_influx("Monolithic_Transformer", result,Infer_latency,requect_latency,cpu_usage,memory_usage,read_bytes,write_bytes,throughtput)

                #producer.send("LSTM_predicitons_Monolithic", value=X)
                

                df_ary = pd.DataFrame()





def process_data1(df,FS,fs,window_size,window_shift,feature_list):

    odp = ProcessData(df,FS,fs,window_size,window_shift,feature_list)
    processed_data = odp.process()

    return processed_data

# Function to save prediction to InfluxDB
def save_to_influx(bucket_name, prediction,Infer_latency,request_latency,cpu_usage,memory_usage,read_bytes,write_bytes,throughtput):
    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    # Get current time
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    
    # Define data point
    json_body = [
        {
            "measurement": "Prediction_result",
            "tags": {},
            "time": current_time,
            "fields": {
                "prediction":prediction,
                "Infer_Latency":Infer_latency,
                "Request_Latency":request_latency,
                "cpu":cpu_usage,
                "Memory":memory_usage,
                "Disk_read":read_bytes,
                "Disk_write":write_bytes,
                "Throghtput":throughtput
                
            }
        }
    ]

    write_api.write(bucket=bucket_name, org="iff", record=json_body)

# Function to save prediction to InfluxDB
def save_to_influx_FE(bucket_name,df):
    json_body = []
    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    
    for index, row in df.iterrows():
        json_body.append({
            "measurement": "EMG Feature",
            "tags": {
                "tag_key": "tag_value"  # Optional, add tags if needed
            },
            "time": pd.Timestamp.utcnow().isoformat(),  # You can specify your own timestamp
            "fields": row.to_dict()
        })

    write_api.write(bucket=bucket_name, org="iff", record=json_body)

# Simulate real-time data processing
while True:
    process_data()



