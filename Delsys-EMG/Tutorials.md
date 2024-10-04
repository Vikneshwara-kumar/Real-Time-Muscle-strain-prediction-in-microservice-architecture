# Delsys EMG System - Setup and Usage Tutorial

## Introduction
This document provides a step-by-step guide on how to set up and use the Delsys EMG system with Python. Follow the instructions carefully to ensure proper installation, configuration, and usage of the system.

## 1. Prerequisites
Before you begin, ensure you have the following:
- A computer running Windows, macOS, or Linux.
- Python 3.12.0 installed on your computer. If not, download and install Python from [Python 3.12.0](https://www.python.org/downloads/release/python-3120/).
- A Delsys Trigno Base Station or Trigno Lite, and the necessary sensors.

## 2. Installation

### Step 1: Install Python
1. Download Python 3.12.0 from [Python 3.12.0](https://www.python.org/downloads/release/python-3120/).
2. Follow the installation instructions provided on the website to install Python on your system.

### Step 2: Clone the Project Repository
1. Navigate to your preferred directory where you want to set up the project.
2. Clone the project repository or download the project files and unzip them.

### Step 3: Install Project Dependencies
1. Open a terminal or command prompt.
2. Navigate to the `/Delsys-Python-Demo` base directory using the following command:
   ```bash
   cd /path/to/Delsys-Python-Demo
   ```
3. Install the necessary dependencies using the following command:
   ```bash
   python -m pip install -r requirements.txt
   ```

### Step 4: Configure License Key
1. Open the file `/AeroPy/TrignoBase.py` in your preferred text editor or IDE.
2. Copy and paste the key/license strings provided by Delsys Inc. during your system purchase into the appropriate section in the file.
3. Save the file and close it.
4. If you encounter any issues, contact [Delsys Support](https://delsys.com/support/).

### Step 5: Set Up Python Interpreter/Virtual Environment
If you are using an IDE (like PyCharm, VSCode, or others):
1. Open your IDE.
2. Set up your Python interpreter or virtual environment within the IDE settings.
3. Ensure the interpreter is pointing to the Python 3.12.0 installation.

## 3. Configuring the MQTT Client

### Step 6: Configure MQTT Settings
1. Open the `/AeroPy/DataManager.py` file in your text editor or IDE.
2. Locate the following section in the script:
   ```python
   class DataKernel():
       def __init__(self, trigno_base):
           self.TrigBase = trigno_base
           self.packetCount = 0
           self.sampleCount = 0
           self.allcollectiondata = [[]]
           self.channel1time = []
           self.collected_data_array = []
           self.mqtt_client = mqtt.Client()
           self.mqtt_broker = "broker.hivemq.com"
           self.mqtt_port = 1883
           self.mqtt_topic ="mqtt-delsys01-source"
   ```
3. Modify the `mqtt_broker`, `mqtt_port`, and `mqtt_topic` variables to match your MQTT broker settings.
4. If you need to add more topics, insert the new topic below the default topic within the `self.mqtt_topic` section.

### Step 7: Adding More Users or Sensors
1. To add more users or sensors, add another `self.collected_data_array = []` line below the default array in the `DataKernel` class.
2. Configure the second sensor by copying the following snippet and renaming it with the suffix `2`:
   ```python
   self.collected_data_array_sensor1 = (data_queue[0][0])
   sensor1 = pd.DataFrame({'EMG': self.collected_data_array_sensor1})
   json_data1 =sensor1.to_json()
   print(len(json_data1))
   self.send_mqtt(json_data1)
   ```
3. Paste the copied snippet into the `def processData(self, data_queue):` function within the `/AeroPy/DataManager.py` script.
4. Save your changes and close the file.

## 4. Running the Application

### Step 8: Prepare the Hardware
1. Ensure that the Trigno base station or Trigno Lite is plugged into a power source and connected to the PC via USB.
2. Power on your sensor(s) by removing them from the charge station and introducing a magnet. The charge station has a built-in magnet under the "lock" symbol at the center of the case.

### Step 9: Running the Application
1. Navigate to the `/Delsys-Python-Demo` directory.
2. Run the application using the following command:
   ```bash
   python DelsysPythonDemo.py
   ```
3. The application will launch, and you should see the Start Menu.

## 5. Using the Application

### Step 10: Collecting Data
1. Click the `Collect Data` button on the Start Menu to open the Data Collection window.
2. Click the `Connect` button to connect the app to the Trigno base station. You should see some log and initialization messages in your terminal.

### Step 11: Pairing and Scanning Sensors
1. If the sensor has not already been paired with the base, click the `Pair` button and introduce a magnet again to initiate pairing.
2. Click the `Scan` button to add your sensor to the application's sensor list.
3. Highlight the sensor by clicking on it, then select its mode from the mode drop-down menu.

### Step 12: Starting and Stopping Data Stream
1. Click the `Start` button to begin the data stream and plotting.
2. To stop the data stream and plotting, click the `Stop` button.

### Step 13: Restarting the Program
To start the program again, close the Data Collection window and run the `DelsysPythonDemo.py` script as described in Step 9.

## 6. Additional Documentation
For more details on configuring modes and other advanced settings, refer to the [AeroPy Documentation](#AeroPy-Documentation).

## 7. Support
If you encounter any issues or have questions, contact [Delsys Support](https://delsys.com/support/) for assistance.

---

This tutorial should guide you through the process of setting up and using the Delsys EMG system with Python. If you follow these steps carefully, you should be able to collect and analyze EMG data efficiently.