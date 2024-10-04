from time import sleep
import json
from json import dumps
import numpy as np
import pandas as pd
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from Feature_extractor import ProcessData  # Ensure this is correctly implemented
from flask import Flask, request, jsonify
from kafka import KafkaConsumer, KafkaProducer
import threading
from collections import deque
import psutil  # For system metrics

# InfluxDB configuration
token = "HPskNZN757ImNKb7CmOtEpfX4y2wD_2jiLNZ_TdXYMyBBUqkFBKMa26rCXaCpNuia-MbW7nSrhe9-DdFzQ_VvA=="
org = "iff"
url = "http://192.168.50.202:8086"
write_client = InfluxDBClient(url=url, token=token, org=org)

KAFKA_BROKER = '192.168.50.234:29093'
subject = {
    'subject1',
    'subject2',
    'subject3'
}

fs = 1000
FS = 2148
window_size = 300
window_shift = 150
feature_list = ['RMS', 'MAV', 'WL', 'ZC', 'MDF', 'MNF', 'MNP', 'SSC']  # List of required features
feature_columns = ['RMS', 'MAV', 'WL', 'SSC', 'MDF', 'MNF', 'MNP', 'PSD', 'stft_feature_1', 'stft_feature_2', 'stft_feature_3']


producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Function to create Kafka consumer
def create_consumer(topic, group_id):
    return KafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BROKER,
        group_id=group_id,
        auto_offset_reset='latest',
        enable_auto_commit=True,
        auto_commit_interval_ms=2000,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )

# Create consumers for each user
consumers = {
    'user1': create_consumer('delsys-source-emg01', '96'),
    'user2': create_consumer('delsys-source-emg02', '97'),
    'user3': create_consumer('delsys-source-emg03', '98')
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
    memory_usage_mb = memory_info.used / (1024 ** 2)  # Convert bytes to MB
    return cpu_usage, memory_usage_mb

def get_disk_io():
    disk_io = psutil.disk_io_counters()
    return disk_io.read_bytes, disk_io.write_bytes

def calculate_throughput(user):
    return sum(throughput_window[user]) / len(throughput_window[user])

# Function to save prediction to InfluxDB
def save_to_influx(bucket_name, df, user):
    json_body = []
    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    for index, row in df.iterrows():
        json_body.append({
            "measurement": "EMG Feature_sacle",
            "tags": {"user": user},
            "time": pd.Timestamp.utcnow().isoformat(),
            "fields": row.to_dict()
        })
    write_api.write(bucket=bucket_name, org="iff", record=json_body)

def save_metrics_to_influx(bucket_name, response_time,throughput,cpu_usage, memory_usage, user):

    json_body = [
        {
            "measurement": "Prediction_result_sacle",
            "tags": {"user": user},
            "time": pd.Timestamp.utcnow().isoformat(),
            "fields": {
                "Execution_time": response_time,
                "cpu_usage": cpu_usage,
                "memory_usage_mb": memory_usage,
                "throughput": throughput
            }
        }
    ]
    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket_name, org="iff", record=json_body)

def process_data(consumer, user):
    for message in consumer:
        start_time = time.time()
        request_counter[user] += 1
        raw_data = message.value
        features = pd.DataFrame(raw_data)
        #print(f"Processing {len(features)} features for {user}")
        odp = ProcessData(features, FS, fs, window_size, window_shift, feature_list)
        processed_data = odp.process()
        #print(f"Processed data for {user}: {processed_data}")

        X1 = processed_data[feature_columns]
        df_json_str = X1.to_json(orient="records")
        df_json_obj = json.loads(df_json_str)

        user_topic = f"{user}_extracted_features"
        print(user_topic)
        producer.send(user_topic, value=df_json_obj)
        response_time = time.time() - start_time
        print(f"Response time for {user}: {response_time}")
        cpu_usage, memory_usage = get_cpu_memory_usage()
        throughput_window[user].append(request_counter[user])
        throughput = calculate_throughput(user)

        # Save Processed data to InfluxDB
        save_to_influx("Microservice_Scaleability", processed_data, user)
        save_metrics_to_influx("Microservice_Scaleability", response_time,throughput,cpu_usage, memory_usage, user)

threads = []
for user, consumer in consumers.items():
    thread = threading.Thread(target=process_data, args=(consumer, user))
    threads.append(thread)
    thread.start()
    

for thread in threads:
    thread.join()
