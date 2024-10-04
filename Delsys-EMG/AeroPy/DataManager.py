"""
This is the class that handles the data that is output from the Delsys Trigno Base.
Create an instance of this and pass it a reference to the Trigno base for initialization.
See CollectDataController.py for a usage example.
"""

import numpy as np
import csv
import pandas as pd
import json
import socket
import time
import paho.mqtt.client as mqtt


class DataKernel():
    def __init__(self, trigno_base):
        self.TrigBase = trigno_base
        self.packetCount = 0
        self.sampleCount = 0
        self.allcollectiondata = [[]]
        self.channel1time = []
        self.collected_data_array = []
        self.collected_data_array_sensor1 = []
        self.mqtt_client = mqtt.Client()
        self.mqtt_broker = "broker.hivemq.com"
        self.mqtt_port = 1883
        self.mqtt_topic ="mqtt-delsys01-source"

        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")

        # UDP setup
        self.udp_ip = "127.0.0.1"
        self.udp_port = 10000
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def processData(self, data_queue):
        """Processes the data from the DelsysAPI and place it in the data_queue argument"""
        outArr = self.GetData()

        if outArr is not None:

            for i in range(len(outArr)):
                self.allcollectiondata[i].extend(outArr[i][0].tolist())
            try:
                for i in range(len(outArr[0])):
                    if np.asarray(outArr[0]).ndim == 1:
                        data_queue.append(list(np.asarray(outArr, dtype='object')[0]))
                    else:
                        data_queue.append(list(np.asarray(outArr, dtype='object')[:, i]))

                    
                    self.collected_data_array_sensor1 = (data_queue[0][0])
                    sensor1 = pd.DataFrame({'EMG': self.collected_data_array_sensor1})
                    json_data1 =sensor1.to_json()
                    print(len(json_data1))
                    self.send_mqtt(json_data1)
                    time.sleep(1)
                    
                    self.collected_data_array.extend(data_queue[0][0])
                    

                    
                try:
                    self.packetCount += len(outArr[0])
                    self.sampleCount += len(outArr[0][0])
                except:
                    pass
            except IndexError:
                pass

    def processYTData(self, data_queue):
        """Processes the data from the DelsysAPI and place it in the data_queue argument"""
        outArr = self.GetYTData()
        print(outArr)
        print("i am printing")
        print(type(outArr))
        if outArr is not None:
            for i in range(len(outArr)):
                self.allcollectiondata[i].extend(outArr[i][0].tolist())
            try:
                yt_outArr = []
                for i in range(len(outArr)):
                    chan_yt = outArr[i]
                    chan_ydata = np.asarray([k.Item2 for k in chan_yt[0]], dtype='object')
                    yt_outArr.append(chan_ydata)

                data_queue.append(list(yt_outArr))
                print("I am True")
                self.collected_data_array.extend(data_queue[0][0])

                try:
                    self.packetCount += len(outArr[0])
                    self.sampleCount += len(outArr[0][0])
                except:
                    pass
            except IndexError:
                pass
        return data_queue

    def GetData(self):
        """ Check if data ready from DelsysAPI via Aero CheckDataQueue() - Return True if data is ready
            Get data (PollData)
            Organize output channels by their GUID keys

            Return array of all channel data
        """

        dataReady = self.TrigBase.CheckDataQueue()                      # Check if DelsysAPI real-time data queue is ready to retrieve
        if dataReady:
            DataOut = self.TrigBase.PollData()                        # Dictionary<Guid, List<double>> (key = Guid (Unique channel ID), value = List(Y) (Y = sample value)
            outArr = [[] for i in range(len(DataOut.Keys))]             # Set output array size to the amount of channels being outputted from the DelsysAPI

            channel_guid_keys = list(DataOut.Keys)                      # Generate a list of all channel GUIDs in the dictionary
            for j in range(len(DataOut.Keys)):                          # loop all channels
                chan_data = DataOut[channel_guid_keys[j]]               # Index a single channels data from the dictionary based on unique channel GUID (key)
                outArr[j].append(np.asarray(chan_data, dtype='object')) # Create a NumPy array of the channel data and add to the output array

            return outArr
        else:
            return None

    def GetYTData(self):
        """ YT Data stream only available when passing 'True' to Aero Start() command i.e. TrigBase.Start(True)
            Check if data ready from DelsysAPI via Aero CheckYTDataQueue() - Return True if data is ready
            Get data (PollYTData)
            Organize output channels by their GUID keys

            Return array of all channel data
        """

        dataReady = self.TrigBase.CheckYTDataQueue()                        # Check if DelsysAPI real-time data queue is ready to retrieve
        if dataReady:
            DataOut = self.TrigBase.PollYTData()                            # Dictionary<Guid, List<(double, double)>> (key = Guid (Unique channel ID), value = List<(T, Y)> (T = time stamp in seconds Y = sample value)
            outArr = [[] for i in range(len(DataOut.Keys))]                 # Set output array size to the amount of channels being outputted from the DelsysAPI

            channel_guid_keys = list(DataOut.Keys)                          # Generate a list of all channel GUIDs in the dictionary
            for j in range(len(DataOut.Keys)):                              # loop all channels
                chan_yt_data = DataOut[channel_guid_keys[j]]                # Index a single channels data from the dictionary based on unique channel GUID (key)
                outArr[j].append(np.asarray(chan_yt_data, dtype='object'))  # Create a NumPy array of the channel data and add to the output array

            return outArr
        else:
            return None
    
    def convert_ndarrays(self, data):
            if isinstance(data, np.ndarray):
                # This handles arrays of any shape, including (174,)
                return data.tolist()
            elif isinstance(data, list):
                # Recursively process each item in the list
                return [self.convert_ndarrays(item) for item in data]
            else:
                # Return the item unchanged if it's neither a list nor a numpy array
                return data
    
    def serialize_to_json(self, data):
        converted_data = self.convert_ndarrays(data)
        json_data = json.dumps(converted_data)
        return json_data

    def send_mqtt(self, data):
        try:
            self.mqtt_client.publish(self.mqtt_topic, data)
        except Exception as e:
            print(f"Failed to publish data via MQTT: {e}")
    
    # Method to send data via UDP
    def send_udp(self, data):
        try:
            message = data  # Convert data to JSON string
            self.udp_socket.sendto(message.encode(), (self.udp_ip, self.udp_port))
            print(f"Sent data via UDP to {self.udp_ip}:{self.udp_port}")
        except Exception as e:
            print(f"Failed to send data via UDP: {e}")


    def saveCollectionData(self, filename="EMG_s1.csv"):
        print("saving data...and building data")
        df = pd.DataFrame({
            'EMG': self.collected_data_array
        })
        print(df)
        df.to_csv(filename, index=False)

        print("Data saved successfully.")


