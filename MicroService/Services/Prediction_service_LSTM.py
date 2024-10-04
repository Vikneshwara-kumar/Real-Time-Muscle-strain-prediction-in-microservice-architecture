from flask import Flask, jsonify
from kafka import KafkaConsumer, KafkaProducer
import json
import threading
from tensorflow.keras.models import load_model
import numpy as np
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from sklearn.preprocessing import StandardScaler
import pickle
import pandas as pd
import psutil
from collections import deque

app = Flask(__name__)

token = "HPskNZN757ImNKb7CmOtEpfX4y2wD_2jiLNZ_TdXYMyBBUqkFBKMa26rCXaCpNuia-MbW7nSrhe9-DdFzQ_VvA=="
org = "iff"
url = "http://192.168.50.202:8086"
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
feature_columns = ['RMS', 'MAV', 'WL', 'SSC', 'MDF', 'MNF', 'MNP', 'PSD', 'stft_feature_1', 'stft_feature_2', 'stft_feature_3']
request_counter = 0
throughput_window = deque(maxlen=60)  # 60 seconds window

# Load the model and scaler
model = load_model('E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/MicroService/lstm.keras')
# Load the scaler from the file
with open('E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/scaler.pkl', 'rb') as file:
    loaded_scaler = pickle.load(file)
print("Scaler has been loaded from 'scaler.pkl'")


KAFKA_BROKER = '192.168.50.234:29093'
NORMALIZED_DATA_TOPIC = 'extracted_features'
PREDICTION_TOPIC = 'predictions'

consumer = KafkaConsumer(
    NORMALIZED_DATA_TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    group_id='200', # Specify the consumer group ID
    auto_offset_reset='latest',       # Set the offset to the beginning of the topic
    enable_auto_commit=True,            # Enable auto commit offsets
    auto_commit_interval_ms=2000,       # Set auto commit interval (in milliseconds)
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  
)

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)



# Function to save prediction to InfluxDB
def save_to_influx(bucket_name, prediction,Infer_latency,request_latency,cpu_usage,memory_usage,read_bytes,write_bytes,throughtput):
    write_api = write_client.write_api(write_options=SYNCHRONOUS)

    # Get current time
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    
    # Define data point
    json_body = [
        {
            "measurement": "Prediction_result_lstm",
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
    try:
        write_api.write(bucket=bucket_name, org="iff", record=json_body)
        print("Data saved to InfluxDB successfully")
    except Exception as e:
        print(f"InfluxDB Write Error: {e}")

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

def consume_and_process():
    df_ary = pd.DataFrame()
    global request_counter
    for message in consumer:
        start_time = time.time()
        request_counter += 1
        data = message.value
        df = pd.DataFrame(data)

        # Append new data to df_ary
        df_ary = pd.concat([df_ary, df], ignore_index=True)

        if len(df_ary)>=30:

            X2 = df_ary.iloc[:30]

            X_scaled = loaded_scaler.transform(X2)

            sequence =  X_scaled.reshape((1,30,11))

            result,Infer_latency = infer(sequence)

            requect_latency = time.time() -start_time
            print(requect_latency)

            cpu_usage, memory_usage = get_cpu_memory_usage()
            read_bytes, write_bytes = get_disk_io()
            throughput_window.append(request_counter)

            throughtput = calculate_throughput()

            save_to_influx("Microservice_LSTM", result,Infer_latency,requect_latency,cpu_usage,memory_usage,read_bytes,write_bytes,throughtput)

            df_ary = pd.DataFrame()

        

thread = threading.Thread(target=consume_and_process)
thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
