import pandas as pd
import time
import paho.mqtt.client as mqtt
import json

def read_sensor_data(filename):
    """
    Reads sensor data from a CSV file and simulates continuous readings.

    Args:
        filename (str): Path to the CSV file containing sensor data.

    Yields:
        dict: A dictionary containing sensor data column names as keys and corresponding values.
    """
    data = pd.read_csv(filename)
    num_rows = len(data)
    current_row = 0

    while True:
        # Get sensor data for the current row
        sensor_data = data.iloc[current_row].to_dict()

        yield sensor_data

        # Move to the next row (loop back to the beginning if necessary)
        current_row = (current_row + 1) % num_rows

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

# MQTT Configuration
broker_address = "broker.hivemq.com"
mqtt_topic = "mqtt-delsys03-source"

# Create MQTT Client
client = mqtt.Client("SensorPublisher")
client.on_connect = on_connect

# Connect to MQTT Broker
client.connect(broker_address)

# Start the MQTT Client
client.loop_start()

# Example usage
if __name__ == "__main__":
    filename = "EMG_emulation_3.csv"  # Replace with your CSV file path

    sensor_data_generator = read_sensor_data(filename)

    while True:
        sensor_data_list = []
        label = None

        # Collect 2148 samples
        for _ in range(2148):
            sensor_data = next(sensor_data_generator)
            sensor_data_list.append(sensor_data)
            # Assuming the label column is named 'Label'
            label = sensor_data.get('Label')

        # Convert sensor data list to JSON string
        sensor_data_json = json.dumps(sensor_data_list)

        # Publish sensor data to MQTT topic
        client.publish(mqtt_topic, sensor_data_json)

        # Print the label and sensor data count to the console
        print(f"Published {len(sensor_data_list)} sensor readings with Label: {label} to {mqtt_topic}")

        # Wait for 1 second to simulate 2148 Hz sampling frequency
        time.sleep(1)
