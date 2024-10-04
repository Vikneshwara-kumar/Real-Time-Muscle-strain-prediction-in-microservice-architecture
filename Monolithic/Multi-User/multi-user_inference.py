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
from Feature_extractor import ProcessData
import paho.mqtt.client as mqtt
from collections import deque
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import pickle
from Feature_extractor import ProcessData  # Ensure this is correctly implemented
import queue
from collections import deque
import psutil
import threading


token = "HPskNZN757ImNKb7CmOtEpfX4y2wD_2jiLNZ_TdXYMyBBUqkFBKMa26rCXaCpNuia-MbW7nSrhe9-DdFzQ_VvA=="
org = "iff"
url = "http://192.168.50.202:8086"
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

fs = 1000
FS = 2148
window_size = 300
window_shift = 150
feature_list = ['RMS', 'MAV', 'WL', 'ZC', 'MDF', 'MNF', 'MNP', 'SSC']  # List of required features
feature_columns = ['RMS', 'MAV', 'WL', 'SSC', 'MDF', 'MNF', 'MNP', 'PSD', 'stft_feature_1', 'stft_feature_2', 'stft_feature_3']


# Load your trained model
current_work_dir = os.getcwd()
MODEL_path = "E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/lstm.keras"
model = load_model(MODEL_path)
# Load the scaler from the file
with open('E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/scaler.pkl', 'rb') as file:
    loaded_scaler = pickle.load(file)
print("Scaler has been loaded from 'scaler.pkl'")

###################################################################################################################################

# Kafka producer setup
producer = KafkaProducer(bootstrap_servers=['192.168.50.234:29093'],
                         value_serializer=lambda x: dumps(x).encode('utf-8'))

# Function to create Kafka consumer
def create_consumer(topic, group_ids):
    return KafkaConsumer(
        topic,
        bootstrap_servers='192.168.50.234:29093',
        group_id=group_ids,
        auto_offset_reset='latest',
        enable_auto_commit=True,
        auto_commit_interval_ms=2000,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

# Create consumers for each user
consumers = {
    'user1': create_consumer('delsys-source-emg01','96'),
    'user2': create_consumer('delsys-source-emg02','97'),
    'user3': create_consumer('delsys-source-emg03','98')
    
}

# Queues for inter-thread communication
message_queues = {user: deque(maxlen=30) for user in consumers.keys()}
throughput_window = {user: deque(maxlen=60) for user in consumers.keys()}
request_counter = {user: 0 for user in consumers.keys()}

# Function to get system metrics
def get_cpu_memory_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent
    memory_usage_mb = memory_usage / (1024 ** 2)  # Convert bytes to MB
    return cpu_usage, memory_usage_mb

def get_disk_io():
    disk_io = psutil.disk_io_counters()
    return disk_io.read_bytes, disk_io.write_bytes

def calculate_throughput(user):
    return sum(throughput_window[user]) / len(throughput_window[user])

def infer(input_data):
    start_time = time.time()
    prediction = model.predict(input_data)
    predicted_class = np.argmax(prediction, axis=-1)
    result = np.ndarray.item(predicted_class)
    end_time = time.time()
    latency = end_time - start_time
    return result, latency

def process_data(consumer, user):
    df_ary = pd.DataFrame()
    while True:
        for message in consumer:
            start_time = time.time()
            request_counter[user] += 1
            data = message.value
            df = pd.DataFrame(data)
            processed = process_data1(df, FS, fs, window_size, window_shift, feature_list)
            X1 = processed[feature_columns]
            df_json_str = processed.to_json(orient="records")
            df_json_obj = json.loads(df_json_str)
            producer.send("EMG_Features_Monolithic", value=df_json_obj)
            save_to_influx_FE("Monolithic_scalability", processed, user)
            df_ary = pd.concat([df_ary, X1], ignore_index=True)
            if len(df_ary) >= 30:
                X2 = df_ary.iloc[:30]
                X_scaled = loaded_scaler.transform(X2)
                sequence = X_scaled.reshape((1, 30, 11))
                result, Infer_latency = infer(sequence)
                request_latency = time.time() - start_time
                cpu_usage, memory_usage = get_cpu_memory_usage()
                read_bytes, write_bytes = get_disk_io()
                throughput_window[user].append(request_counter[user])
                throughput = calculate_throughput(user)
                save_to_influx("Monolithic_scalability", result, Infer_latency, request_latency, cpu_usage, memory_usage, read_bytes, write_bytes, throughput, user)
                df_ary = pd.DataFrame()

def process_data1(df, FS, fs, window_size, window_shift, feature_list):
    odp = ProcessData(df, FS, fs, window_size, window_shift, feature_list)
    processed_data = odp.process()
    return processed_data

# Function to save prediction to InfluxDB
def save_to_influx(bucket_name, prediction, Infer_latency, request_latency, cpu_usage, memory_usage, read_bytes, write_bytes, throughput, user):
    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json_body = [
        {
            "measurement": "Prediction_result",
            "tags": {"user": user},
            "time": current_time,
            "fields": {
                "prediction": prediction,
                "Infer_Latency": Infer_latency,
                "Request_Latency": request_latency,
                "cpu": cpu_usage,
                "Memory": memory_usage,
                "Disk_read": read_bytes,
                "Disk_write": write_bytes,
                "Throughput": throughput
            }
        }
    ]
    write_api.write(bucket=bucket_name, org="iff", record=json_body)

def save_to_influx_FE(bucket_name, df, user):
    json_body = []
    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    for index, row in df.iterrows():
        json_body.append({
            "measurement": "EMG Feature",
            "tags": {"user": user},
            "time": pd.Timestamp.utcnow().isoformat(),
            "fields": row.to_dict()
        })
    write_api.write(bucket=bucket_name, org="iff", record=json_body)

# Start threads for each consumer
threads = []
for user, consumer in consumers.items():
    thread = threading.Thread(target=process_data, args=(consumer, user))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()