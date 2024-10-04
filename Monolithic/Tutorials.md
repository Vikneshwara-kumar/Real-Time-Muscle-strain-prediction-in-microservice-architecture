# Tutorial: Deploying an LSTM Model in a Monolithic Architecture

This tutorial will guide you through the steps to deploy an LSTM model using a monolithic architecture. The deployment involves real-time data processing, prediction using a pre-trained model, and saving the results to an InfluxDB database. The system also uses Kafka for message brokering and MQTT for communication.

## Prerequisites

Before you start, ensure that you have the following:

- Python 3.8 or higher installed.
- Kafka server set up and running.
- InfluxDB server set up and running.
- A trained LSTM model and associated scaler saved in `.h5` and `.pkl` files respectively.
- Required Python packages installed using the `requirements.txt` file.

## 1. Project Setup

### Step 1: Install Required Packages

Ensure you have all the necessary Python packages installed. Save the following content into a `requirements.txt` file and install the dependencies:

Install the packages using pip:

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Kafka and InfluxDB

Ensure that your Kafka broker and InfluxDB server are running. Kafka is used for messaging between different components, while InfluxDB stores the predictions and other relevant data.

- **Kafka**: Set up topics for receiving raw data and sending predictions.
- **InfluxDB**: Create a bucket where the prediction results and features will be stored.

## 2. Code Overview

The provided code does the following:

- **Consumes EMG data from a Kafka topic.**
- **Processes the data in real-time** using a pre-trained LSTM model.
- **Publishes predictions** to another Kafka topic.
- **Stores the predictions and latency information** in InfluxDB.
- **Rescales data** using a pre-saved scaler before feeding it to the model.

## 3. Running the Code

### Step 1: Define Your Configuration

Make sure the following variables in your code are correctly configured:

```python
# InfluxDB configuration
token = "Your_InfluxDB_Token"
org = "Your_Org"
url = "http://Your_InfluxDB_URL"
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

# Kafka configuration
producer = KafkaProducer(bootstrap_servers=['Your_Kafka_Broker_URL'],
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'))

consumer = KafkaConsumer(
    'Your_Input_Topic',                  # Specify the topic name
    bootstrap_servers='Your_Kafka_Broker_URL', # Specify the Kafka broker(s)
    group_id='Your_Group_ID', # Specify the consumer group ID
    auto_offset_reset='latest',       # Set the offset to the latest in the topic
    enable_auto_commit=True,            # Enable auto commit offsets
    auto_commit_interval_ms=1000,       # Set auto commit interval (in milliseconds)
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))  
)
```

### Step 2: Load Your Model and Scaler

Ensure the paths to your saved LSTM model and scaler are correct:

```python
# Load your trained model
MODEL_path = "path_to_your_model/lstm.keras"
model = load_model(MODEL_path)

# Load the scaler from the file
with open('path_to_your_scaler/scaler.pkl', 'rb') as file:
    loaded_scaler = pickle.load(file)
print("Scaler has been loaded from 'scaler.pkl'")
```

### Step 3: Process Data and Make Predictions

The `process_data` function consumes data from Kafka, processes it, and makes predictions using the LSTM model. It then sends the predictions back to Kafka and stores them in InfluxDB.

```python
def process_data():
    df_ary = pd.DataFrame()

    while True:
        for message in consumer:
            start_time = time.time()
            data = message.value
            df = pd.DataFrame(data)

            # Send raw data to Kafka and save to InfluxDB
            producer.send("Your_Output_Topic", value=df.to_json(orient="records"))
            save_to_influx_FE("Your_InfluxDB_Bucket", df)

            # Append new data and check for sufficient data for prediction
            df_ary = pd.concat([df_ary, df], ignore_index=True)

            if len(df_ary) >= 30:
                df_to_predict = df_ary.iloc[:30]
                df_array = df_to_predict.to_numpy().reshape((1, 30, 20))
                df_to_predict = scaleing(df_array)
                prediction = predict_with_model(df_array)

                # Clear the buffer after prediction
                df_ary = pd.DataFrame()

                end_time = time.time()
                latency = end_time - start_time
                print(f"Latency: {latency} seconds")
```

### Step 4: Scaling and Prediction Functions

The data is scaled using a pre-saved scaler before being fed into the model:

```python
def scaleing(data):
    original_train_shape = data.shape
    X_flattened = data.reshape(-1, original_train_shape[2])
    X_scaled = loaded_scaler.transform(X_flattened)
    data_scaled = X_scaled.reshape(original_train_shape)
    return data_scaled

def predict_with_model(data):
    start_time = time.time()
    prediction = model.predict(data)
    end_time = time.time()
    results = np.argmax(prediction, axis=1)
    final_prediction = classify_result(results)
    producer.send("Your_Prediction_Topic", value=np.ndarray.item(results))
    save_to_influx("Your_InfluxDB_Bucket", np.ndarray.item(results), end_time - start_time)
    return final_prediction
```

### Step 5: Storing Data in InfluxDB

The `save_to_influx` function stores predictions and latency in InfluxDB:

```python
def save_to_influx(bucket_name, prediction, latency):
    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    current_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    json_body = [
        {
            "measurement": "Prediction_result",
            "time": current_time,
            "fields": {
                "prediction": prediction,
                "latency": latency,
            }
        }
    ]
    write_api.write(bucket=bucket_name, org="Your_Org", record=json_body)
```

### Step 6: Run the Script

Finally, run your script:

```bash
python model_inference_LSTM.py
```

This will start the data processing loop, where the script will continuously consume data from Kafka, process it using the LSTM model, and save the results to InfluxDB.

## 4. Monitoring and Troubleshooting

- **Kafka Monitoring**: Ensure that the Kafka brokers are running, and check the logs for any issues with message processing.
- **InfluxDB Monitoring**: Verify that data is being correctly written to the database by querying the relevant buckets.
- **Logs**: Add print statements or use logging to monitor the performance and behavior of your script.

## Conclusion

This tutorial has walked you through the process of setting up, configuring, and running an LSTM model deployment in a monolithic architecture. With the provided script, you can process real-time data, make predictions, and store the results for further analysis. Adjust the code as needed to suit your specific environment and use case.