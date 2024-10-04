# Tutorial: Deploying LSTM Model in a Microservice Architecture

This tutorial will guide you through the deployment of an LSTM model in a microservice architecture. The deployment consists of three microservices: a **Feature Extraction Service**, a **Prediction Service**, and a **Data Storage Service**. These services communicate through Kafka and store data in InfluxDB.

## Prerequisites

Before starting, ensure that you have:

- Python 3.8 or higher installed.
- Kafka server set up and running.
- InfluxDB server set up and running.
- The required Python packages installed using the `requirements.txt` file provided.

## 1. Project Setup

### Step 1: Install Required Packages

Install the packages using pip:

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Kafka and InfluxDB

Ensure that your Kafka broker and InfluxDB server are running. Kafka will handle message brokering between microservices, while InfluxDB will store data such as extracted features, predictions, and system metrics.

- **Kafka**: Set up topics for raw data, extracted features, and predictions.
- **InfluxDB**: Create a database or bucket where the data will be stored.

## 2. Overview of Microservices

### Microservice 1: Feature Extraction Service

- **Purpose**: This service consumes raw EMG data from a Kafka topic, extracts features, and publishes the processed data to another Kafka topic.
- **File**: `Feature_extraction_service.py`

### Microservice 2: Prediction Service

- **Purpose**: This service consumes extracted features, normalizes them, and feeds them into a pre-trained LSTM model to make predictions. It then publishes the predictions to another Kafka topic and stores relevant metrics in InfluxDB.
- **File**: `Prediction_service_LSTM.py`

### Microservice 3: Data Storage Service

- **Purpose**: This service exposes several REST endpoints to store different types of data (raw data, features, normalized data, predictions) into InfluxDB.
- **File**: `Data_storage_service.py`

## 3. Running the Microservices

### Step 1: Configure and Run the Feature Extraction Service

1. Open `Feature_extraction_service.py`.
2. Ensure that the Kafka broker, InfluxDB connection details, and topic names are correctly configured:

   ```python
   KAFKA_BROKER = 'Your_Kafka_Broker_URL'
   RAW_DATA_TOPIC = 'delsys-source-emg01'
   EXTRACTED_FEATURES_TOPIC = 'extracted_features'

   token = "Your_InfluxDB_Token"
   org = "Your_Org"
   url = "http://Your_InfluxDB_URL"
   ```

3. Start the service by running the following command:

   ```bash
   python Feature_extraction_service.py
   ```

   This service will listen to the raw data topic, process the data, and send the extracted features to the `extracted_features` topic in Kafka.

### Step 2: Configure and Run the Prediction Service

1. Open `Prediction_service_LSTM.py`.
2. Ensure that the Kafka broker, InfluxDB connection details, and topic names are correctly configured:

   ```python
   KAFKA_BROKER = 'Your_Kafka_Broker_URL'
   NORMALIZED_DATA_TOPIC = 'extracted_features'
   PREDICTION_TOPIC = 'predictions'

   token = "Your_InfluxDB_Token"
   org = "Your_Org"
   url = "http://Your_InfluxDB_URL"
   ```

3. Ensure the correct paths to your trained LSTM model and scaler:

   ```python
   model = load_model('path_to_your_model/lstm.keras')
   with open('path_to_your_scaler/scaler.pkl', 'rb') as file:
       loaded_scaler = pickle.load(file)
   ```

4. Start the service by running the following command:

   ```bash
   python Prediction_service_LSTM.py
   ```

   This service will listen to the `extracted_features` topic, normalize the data, make predictions, and store the results and metrics in InfluxDB.

### Step 3: Configure and Run the Data Storage Service

1. Open `Data_storage_service.py`.
2. Ensure that the InfluxDB connection details are correctly configured:

   ```python
   INFLUXDB_ADDRESS = 'localhost'
   INFLUXDB_PORT = 8086
   INFLUXDB_USER = 'your_user'
   INFLUXDB_PASSWORD = 'your_password'
   INFLUXDB_DATABASE = 'emg_data'
   ```

3. Start the service by running the following command:

   ```bash
   python Data_storage_service.py
   ```

   This service will expose several REST endpoints to store raw data, features, normalized data, and predictions in InfluxDB.

### Step 4: Testing the Setup

You can test the setup by sending raw EMG data to the `RAW_DATA_TOPIC` in Kafka. This data will be processed by the Feature Extraction Service, and the extracted features will be sent to the Prediction Service. The results and metrics will be stored in InfluxDB and can be accessed via the Data Storage Service's REST API.

## 4. Monitoring and Troubleshooting

- **Kafka Monitoring**: Ensure that the Kafka topics are correctly set up and that messages are being passed between the services.
- **InfluxDB Monitoring**: Verify that data is being correctly written to the database by querying the relevant databases or buckets.
- **Logs**: Use print statements or a logging framework to monitor the performance and behavior of each microservice.

## Conclusion

This tutorial has guided you through the process of setting up and running an LSTM model in a microservice architecture. The system is designed for scalability and modularity, allowing each service to be independently managed and deployed. Adjust the code and configurations as needed to suit your specific environment and use case.