# Comprehensive Tutorial: Deploying an LSTM Model in Both Monolithic and Microservice Architectures

This tutorial will guide you through the setup and deployment of an LSTM model for EMG data processing in both monolithic and microservice architectures. It includes setting up your environment, installing necessary dependencies, running the services, and handling the data flow.

## Prerequisites

Before you begin, ensure that you have:

- A machine running Ubuntu (or any other Linux distribution).
- Python 3.8 or higher installed.
- Basic understanding of Python and working with virtual environments.
- Kafka and InfluxDB set up and running (for microservice architecture).
- The necessary scripts from your codebase.

## 1. Setup: Installing Python and Dependencies

### Step 1: Compile All Requirements into One `requirements.txt` File

Here is the compiled `requirements.txt` file that includes all the necessary dependencies:

```plaintext
PySide6
Vispy
Scipy
pythonnet
numpy>=1.21.0
paho.mqtt.client 
time
socket
pandas>=1.3.0
csv
json
matplotlib>=3.4.0
libemg
scipy>=1.7.0
pywavelets>=1.1.1
plotly>=5.0.0
seaborn>=0.11.0
scikit-learn>=0.24.0
tensorflow>=2.5.0
kafka-python>=2.0.2
influxdb-client>=1.23.0
flask>=2.0.0
psutil>=5.8.0
```

### Step 2: Bash Script to Install Python, Create a Virtual Environment, and Install Dependencies

Save the following bash script as `setup_environment.sh`. This script automates the installation of Python (if not already installed), creates a virtual environment, and installs the dependencies from the `requirements.txt` file.

```bash
#!/bin/bash

# Update package list and install prerequisites
sudo apt-get update

# Install Python 3 and pip if not already installed
sudo apt-get install -y python3 python3-pip python3-venv

# Verify Python installation
python3 --version
pip3 --version

# Create a virtual environment
python3 -m venv emg_env

# Activate the virtual environment
source emg_env/bin/activate

# Install dependencies from requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

# Confirm the installation
pip list

echo "Virtual environment setup complete. All dependencies are installed."

# Deactivate the virtual environment
deactivate
```

### How to Use the Script

1. **Save the Compiled `requirements.txt`**:
   - Save the compiled `requirements.txt` file to your project directory.

2. **Save the Bash Script**:
   - Save the bash script to a file named `setup_environment.sh`.

3. **Run the Bash Script**:
   - Open a terminal in your project directory.
   - Make the script executable: 
     ```bash
     chmod +x setup_environment.sh
     ```
   - Run the script:
     ```bash
     ./setup_environment.sh
     ```

The script will install Python (if not already installed), create a virtual environment, and install all the necessary dependencies.

## 2. Monolithic Architecture Deployment

### Overview

In the monolithic architecture, all components are bundled together in a single script. The LSTM model processes EMG data in real-time, making predictions that are stored in InfluxDB.

### Step 1: Set Up Kafka and InfluxDB

Ensure Kafka and InfluxDB are installed and running on your system. You will need to create appropriate topics in Kafka and databases in InfluxDB.

### Step 2: Load Your Model and Scaler

In your script (`model_inference_LSTM.py`), ensure the correct paths to your trained LSTM model and scaler:

```python
# Load your trained model
MODEL_path = "path_to_your_model/lstm.keras"
model = load_model(MODEL_path)

# Load the scaler from the file
with open('path_to_your_scaler/scaler.pkl', 'rb') as file:
    loaded_scaler = pickle.load(file)
```

### Step 3: Run the Monolithic Script

Run your script using the following command:

```bash
python model_inference_LSTM.py
```

This script will start the data processing loop, consuming data from Kafka, making predictions with the LSTM model, and storing results in InfluxDB.

## 3. Microservice Architecture Deployment

### Overview

In the microservice architecture, the application is divided into smaller, independent services:

1. **Feature Extraction Service**: Processes raw EMG data and extracts features.
2. **Prediction Service**: Normalizes the data and uses an LSTM model to make predictions.
3. **Data Storage Service**: Provides REST APIs to store various data in InfluxDB.

### Step 1: Configure and Run the Feature Extraction Service

1. Open `Feature_extraction_service.py`.
2. Ensure that Kafka, InfluxDB, and topic names are correctly configured:

   ```python
   KAFKA_BROKER = 'Your_Kafka_Broker_URL'
   RAW_DATA_TOPIC = 'delsys-source-emg01'
   EXTRACTED_FEATURES_TOPIC = 'extracted_features'
   ```

3. Start the service:

   ```bash
   python Feature_extraction_service.py
   ```

### Step 2: Configure and Run the Prediction Service

1. Open `Prediction_service_LSTM.py`.
2. Ensure that Kafka, InfluxDB, and topic names are correctly configured:

   ```python
   KAFKA_BROKER = 'Your_Kafka_Broker_URL'
   NORMALIZED_DATA_TOPIC = 'extracted_features'
   PREDICTION_TOPIC = 'predictions'
   ```

3. Ensure the correct paths to your trained LSTM model and scaler:

   ```python
   model = load_model('path_to_your_model/lstm.keras')
   with open('path_to_your_scaler/scaler.pkl', 'rb') as file:
       loaded_scaler = pickle.load(file)
   ```

4. Start the service:

   ```bash
   python Prediction_service_LSTM.py
   ```

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

3. Start the service:

   ```bash
   python Data_storage_service.py
   ```

This service will expose several REST endpoints to store raw data, features, normalized data, and predictions in InfluxDB.

### Step 4: Testing the Setup

You can test the setup by sending raw EMG data to the `RAW_DATA_TOPIC` in Kafka. This data will be processed by the Feature Extraction Service, and the extracted features will be sent to the Prediction Service. The results and metrics will be stored in InfluxDB and can be accessed via the Data Storage Service's REST API.

## 4. Monitoring and Troubleshooting

- **Kafka Monitoring**: Ensure that Kafka topics are correctly set up and messages are flowing between services.
- **InfluxDB Monitoring**: Verify that data is being correctly written to the database by querying the relevant databases or buckets.
- **Logs**: Add logging to your scripts to monitor their performance and behavior.

## Conclusion

This tutorial has guided you through the process of setting up, configuring, and running an LSTM model deployment in both monolithic and microservice architectures. The provided scripts and instructions are designed to help you efficiently manage and deploy your EMG data processing system. Adjust the configurations and code as needed to suit your specific environment and use case.