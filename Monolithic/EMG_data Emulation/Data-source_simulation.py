import pandas as pd
import time
import paho.mqtt.client as mqtt
import json
import keyboard

# Function to read CSV file and return as a DataFrame
def read_csv(file_path):
    return pd.read_csv(file_path)

# Function to transmit data points in chunks at a specified sampling rate
def transmit_data(df, topic, broker, port=1883, sampling_rate=2148):
    # Initialize MQTT client
    client = mqtt.Client()
    client.connect(broker, port, 60)

    # Calculate the delay between each data point transmission
    delay = 1  # 1 second delay for 2148 Hz sampling rate

    try:
        num_samples = len(df)
        for i in range(0, num_samples, sampling_rate):
            # Check if space bar is pressed to quit the loop
            if keyboard.is_pressed('space'):
                print("Space bar pressed. Exiting...")
                break

            # Get the current chunk
            chunk = df.iloc[i:i + sampling_rate]

            # Convert the chunk to a list of dictionaries
            chunk_list = chunk.to_dict(orient='records')

            # Convert the list to JSON
            message = json.dumps(chunk_list)
            client.publish(topic, message)
            print(f"Transmitted chunk starting at index {i}")

            # Sleep for the specified delay
            time.sleep(delay)
    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        # Disconnect the MQTT client
        client.disconnect()

if __name__ == "__main__":
    # Path to your CSV file
    csv_file_path = 'E:/Semester/Thesis/Software/Example-Applications-main/Real-Time Transmission/Monolithic/Trial-1.csv'

    # Read the CSV file into a DataFrame
    data_df = read_csv(csv_file_path)

    # MQTT Configuration
    mqtt_topic = 'mqtt-data-source'
    mqtt_broker = 'broker.hivemq.com'
    broker = "broker.hivemq.com"  # Example public broker

    # Transmit data from the CSV file
    transmit_data(data_df, mqtt_topic, mqtt_broker)
