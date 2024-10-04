"""
This class creates an instance of the Trigno base. Put your key and license here.
"""
import threading
import time
from pythonnet import load
load("coreclr")
import clr

clr.AddReference("resources\DelsysAPI")
clr.AddReference("System.Collections")

from Aero import AeroPy

key = "MIIBKjCB4wYHKoZIzj0CATCB1wIBATAsBgcqhkjOPQEBAiEA/////wAAAAEAAAAAAAAAAAAAAAD///////////////8wWwQg/////wAAAAEAAAAAAAAAAAAAAAD///////////////wEIFrGNdiqOpPns+u9VXaYhrxlHQawzFOw9jvOPD4n0mBLAxUAxJ02CIbnBJNqZnjhE50mt4GffpAEIQNrF9Hy4SxCR/i85uVjpEDydwN9gS3rM6D0oTlF2JjClgIhAP////8AAAAA//////////+85vqtpxeehPO5ysL8YyVRAgEBA0IABLd5spxPc5M5yfu17aVC3JZ9W9ykeLe10vu2Zx5sYAhhfetPy6qOb0mLo5AZK8XOUdc3IEshC4zf4BnOpEIxvWk=";
license = "<License>  <Id>f4ab0ac9-18b2-4db8-8b10-5b780658e633</Id>  <Type>Standard</Type>  <Quantity>10</Quantity>  <LicenseAttributes>    <Attribute name='Software'></Attribute>  </LicenseAttributes>  <ProductFeatures>    <Feature name='Sales'>True</Feature>    <Feature name='Billing'>False</Feature>  </ProductFeatures>  <Customer>    <Name>University of Stuttgart</Name>    <Email>nelson.enrique.bances.purizaca@ipa.fraunhofer.de</Email>  </Customer>  <Expiration>Thu, 13 Jan 2033 00:00:00 GMT</Expiration>  <Signature>MEUCIQCw2XHskApHmyBpDRKf8t60f4k3mqNCHs/AdllwDfUzbAIgQsnxjSvpFglIOiqJNMCkPmt4KaKeCywoZEOPWz9OVwY=</Signature></License>";

class TrignoBase():
    """
    AeroPy reference imported above then instantiated in the constructor below
    All references to TrigBase. call an AeroPy method (See AeroPy documentation for details)
    """

    def __init__(self, collection_data_handler):
        self.TrigBase = AeroPy()
        self.collection_data_handler = collection_data_handler
        self.channelcount = 0
        self.pairnumber = 0

    # -- AeroPy Methods --
    def PipelineState_Callback(self):
        return self.TrigBase.GetPipelineState()

    def Connect_Callback(self):
        """Callback to connect to the base"""
        self.TrigBase.ValidateBase(key, license)

    def Pair_Callback(self):
        return self.TrigBase.PairSensor(self.pair_number)

    def CheckPairStatus(self):
        return self.TrigBase.CheckPairStatus()

    def CheckPairComponentAdded(self):
        return self.TrigBase.CheckPairComponentAdded()

    def Scan_Callback(self):
        """Callback to tell the base to scan for any available sensors"""
        try:
            f = self.TrigBase.ScanSensors().Result
        except Exception as e:
            print("Python demo attempt another scan...")
            time.sleep(1)
            self.Scan_Callback()

        self.all_scanned_sensors = self.TrigBase.GetScannedSensorsFound()
        print("Sensors Found:\n")
        for sensor in self.all_scanned_sensors:
            print("(" + str(sensor.PairNumber) + ") " +
                sensor.FriendlyName + "\n" +
                sensor.Configuration.ModeString + "\n")

        self.SensorCount = len(self.all_scanned_sensors)
        for i in range(self.SensorCount):
            self.TrigBase.SelectSensor(i)

        return self.all_scanned_sensors


    def Start_Callback(self, start_trigger, stop_trigger):
        """Callback to start the data stream from Sensors"""
        self.start_trigger = start_trigger
        self.stop_trigger = stop_trigger

        configured = self.ConfigureCollectionOutput()
        if configured:
            #(Optional) To get YT data output pass 'True' to Start method
            self.TrigBase.Start(self.collection_data_handler.streamYTData)
            self.collection_data_handler.threadManager(self.start_trigger, self.stop_trigger)

    def ConfigureCollectionOutput(self):
        if not self.start_trigger:
            self.collection_data_handler.pauseFlag = False

        self.collection_data_handler.DataHandler.packetCount = 0
        self.collection_data_handler.DataHandler.allcollectiondata = [[]]

        # Pipeline Armed when TrigBase.Configure already called.
        # This if block allows for sequential data streams without reconfiguring the pipeline each time.
        # Reset output data structure before starting data stream again
        if self.TrigBase.GetPipelineState() == 'Armed':
            self.collection_data_handler.DataHandler.collected_data_array.append([])
            for i in range(len(self.channelobjects)):
                self.collection_data_handler.DataHandler.allcollectiondata.append([])
            return True


        # Pipeline Connected when sensors have been scanned in sucessfully.
        # Configure output data using TrigBase.Configure and pass args if you are using a start and/or stop trigger
        elif self.TrigBase.GetPipelineState() == 'Connected':
            self.channelcount = 0
            self.TrigBase.Configure(self.start_trigger, self.stop_trigger)
            configured = self.TrigBase.IsPipelineConfigured()
            if configured:
                self.channelobjects = []
                self.plotCount = 0
                self.emgChannelsIdx = []
                globalChannelIdx = 0

                for i in range(self.SensorCount):

                    selectedSensor = self.TrigBase.GetSensorObject(i)
                    print("(" + str(selectedSensor.PairNumber) + ") " + str(selectedSensor.FriendlyName))

                    if len(selectedSensor.TrignoChannels) > 0:
                        print("--Channels")

                        for channel in range(len(selectedSensor.TrignoChannels)):
                            sample_rate = round(selectedSensor.TrignoChannels[channel].SampleRate, 3)
                            print("sample rate",sample_rate)
                            print("----" + selectedSensor.TrignoChannels[channel].Name + " (" + str(sample_rate) + " Hz)")
                            self.channelcount += 1
                            self.channelobjects.append(channel)
                            self.collection_data_handler.DataHandler.allcollectiondata.append([])

                            # NOTE: Plotting/Data Output: This demo does not plot non-EMG channel types such as
                            # accelerometer, gyroscope, magnetometer, and others. However, the data from channels
                            # that are excluded from plots are still available via output from PollData()

                            # ---- Plot EMG Channels
                            if "EMG" in selectedSensor.TrignoChannels[channel].Name:
                                self.emgChannelsIdx.append(globalChannelIdx)
                                self.plotCount += 1

                            # ---- Exclude non-EMG channels from plots
                            else:
                                pass

                            globalChannelIdx += 1

                if self.collection_data_handler.EMGplot:
                    self.collection_data_handler.EMGplot.initiateCanvas(None, None, self.plotCount, 1, 20000)

                return True
        else:
            return False

    def Stop_Callback(self):
        """Callback to stop the data stream"""
        self.collection_data_handler.pauseFlag = True
        self.TrigBase.Stop()

        print("saving data...")
        self.collection_data_handler.DataHandler.saveCollectionData()
        #self.collection_data_handler.DataHandler.saveCollectionData1()
        #self.collection_data_handler.DataHandler.saveCollectionData2()
        #self.collection_data_handler.DataHandler.saveCollectionData3()
        #self.collection_data_handler.DataHandler.savecombineddata()

        #print("Data Collection Complete")

    # ---------------------------------------------------------------------------------
    # ---- Helper Functions
    def getSampleModes(self, sensorIdx):
        """Gets the list of sample modes available for selected sensor"""
        sampleModes = self.TrigBase.AvailibleSensorModes(sensorIdx)
        return sampleModes

    def getCurMode(self, sensorIdx):
        """Gets the current mode of the sensors"""
        curModes = self.TrigBase.GetCurrentSensorMode(sensorIdx)
        return curModes

    def setSampleMode(self, curSensor, setMode):
        """Sets the sample mode for the selected sensor"""
        self.TrigBase.SetSampleMode(curSensor, setMode)
