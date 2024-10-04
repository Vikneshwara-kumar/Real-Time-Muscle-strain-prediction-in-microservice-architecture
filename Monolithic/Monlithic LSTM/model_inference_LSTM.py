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
import queue

token = "HPskNZN757ImNKb7CmOtEpfX4y2wD_2jiLNZ_TdXYMyBBUqkFBKMa26rCXaCpNuia-MbW7nSrhe9-DdFzQ_VvA=="
org = "iff"
url = "http://192.168.50.202:8086"
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)


# Load your trained model
current_work_dir = os.getcwd()
MODEL_path = "E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/lstm.keras"
model = load_model(MODEL_path)
# Load the scaler from the file
with open('E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/scaler.pkl', 'rb') as file:
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
    group_id='14', # Specify the consumer group ID
    auto_offset_reset='latest',       # Set the offset to the beginning of the topic
    enable_auto_commit=True,            # Enable auto commit offsets
    auto_commit_interval_ms=1000,       # Set auto commit interval (in milliseconds)
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  
    )   

# Queues for inter-thread communication
message_queue = queue.Queue()
processed_data_queue = queue.Queue()

def process_data():
    df_ary = pd.DataFrame()

    buffer = []

    while True:
        for message in consumer:
            start_time = time.time()
            data = message.value
            df = pd.DataFrame(data)

            df_json_str = df.to_json(orient="records")
            df_json_obj = json.loads(df_json_str)

            producer.send("EMG_Features_Monolithic", value=df_json_obj )
            save_to_influx_FE("Monolithic_lstm", df)

            # Append new data to df_ary
            df_ary = pd.concat([df_ary, df], ignore_index=True)
            

            # Check if df_ary has reached 50 rows
            if len(df_ary) >= 30:
                # Ensure we only use the first 50 rows
                df_to_predict = df_ary.iloc[:30]
                
                #print(df_to_predict)

                # Convert to numpy array and reshape for the model
                df_array = df_to_predict.to_numpy()
                df_array = df_array.reshape((1, 30, 20))
                df_to_predict = scaleing(df_array)
                print(df_to_predict)
                

                prediction = predict_with_model(df_array)



                # Clear df_ary after prediction
                df_ary = pd.DataFrame()

            # Calculate and print latency
                end_time = time.time()
                latency = end_time - start_time
           
                print(f"Latency: {latency} seconds")

def scaleing(data):
    # Apply the same transformation to the test data
    # Assuming X_train and X_test are your datasets
    # Let's assume original X_train and X_test shapes are obtained and stored before any modification
    original_train_shape = data.shape  # Should be (samples, timesteps, features)
    #print(original_train_shape)
    # Flatten the data for scaling: (samples * timesteps, features)
    X_flattened = data.reshape(-1, original_train_shape[2])  # Flatten keeping the last dim

    # Apply the same transformation to the test data
    X_scaled = loaded_scaler.transform(X_flattened)

    # Reshape the scaled data back to the original dimensions
    data_scaled = X_scaled.reshape(original_train_shape)

    return data_scaled

def predict_with_model(data):
    start_time = time.time()
    prediction = model.predict(data)
    end_time = time.time()
    results= np.argmax(prediction,axis=1)
    print(results)
    final_prediction = classify_result(results)
    print(final_prediction)
    X = np.ndarray.item(results)
    print(type(X))


    producer.send("LSTM_predicitons_Monolithic", value=X)
    latency = end_time - start_time
    save_to_influx("Monolithic_latency", X,latency)
    print(type(latency))

    return


def classify_result(result):
    if result == 0:
        return 'resting'
    elif result == 1:
        return 'low strain'
    elif result == 2:
        return 'medium strain'
    elif result == 3:
        return 'high strain'
    else:
        return 'unknown'
    

# Function to save prediction to InfluxDB
def save_to_influx(bucket_name, prediction,latency):
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
                "latency": latency,
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



