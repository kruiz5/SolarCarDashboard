# 1/20/2020 Changelog
# Copied structure from CAN.py
# Added conversion of BMS messages' signals to actual values.

""" To be used when testing with actual ECUs. """
import can
import can.interfaces
import subprocess
import traceback
from can.interface import Bus
from can import Message
from subprocess import call


class CAN_Control():
    def __init__(self):
        self.bus = None
        self.bufferedReader = None
        self.notifier = None
        self.BMS = self.BMS_Control()
        self.MCU = self.MCU_Control()
        self.Blinkers = self.Blinkers_Control()
        self.initCAN()

    def initCAN(self):
        """Initialize the profile for the CAN controller."""
        try:
            # send out command to set up can0 from the shell to interface CAN controller hardware
            call('sudo ip link set can0 up type can bitrate 500000', shell=True)

            # initialize Bus object
            self.bus = Bus(channel='can0', bustype='socketcan_native')

            # initialize message buffer to store incoming CAN messages
            self.bufferedReader = can.BufferedReader()

            # notifier will notify when new message arrives on the bus and places it in the buffer
            self.notifier = can.Notifier(self.bus, [self.bufferedReader])
        except:
            print(traceback.print_exc())

    def readMessage(self, timeout=0.1):
        """Grabs a message from the buffered reader and returns the arbitration ID and data fields"""
        try:
            arbitrationID = None
            data = None
            msg = self.bufferedReader.get_message(timeout=timeout)
            if msg is not None:
                # arbitration id is the priority number of the CAN message. the lower the id, the higher the priority
                arbitrationID = msg.arbitration_id

                # data is a list of bytes. data[0] is byte 1 ..... all the way to data[7] is byte 8
                data = msg.data
            return arbitrationID, data

        except:
            print(traceback.print_exc())

    def sendMessage(self, msg, timeout=0.1):
        """Sends a CAN message on the bus."""
        try:
            self.bus.send(msg, timeout=timeout)
        except:
            print(traceback.print_exc())

    class BMS_Control():
        def __init__(self):
            # BMS CAN message1
            self.msg1ID = 0x001
            self.failsafeStat = 0
            self.voltage = 0  # instantaneous voltage of battery pack
            self.current = 0  # instantaneous current battery pack
            self.highestTemperature = 0  # current highest temperature of pack
            self.highestTemperatureThermistorID = 0  # id of thermistor with highest temperature

            # BMS CAN message2
            self.msg2ID = 0x002
            self.avgPackCurrent = 0  # average temperature of pack
            self.avgBatteryTemperature = 0  # average temperature of pack
            self.stateOfCharge = 0  # state of charge
            self.fanSpeed = 0 # speed of battery fan

            # others
            self.milesRange = 0

        def getVoltage(self):
            return self.voltage

        def getCurrent(self):
            return self.current

        def getHighestTemp(self):
            return self.highestTemperature

        def getHighetTempThermistorID(self):
            return self.highestTemperatureThermistorID

        def getSOC(self):
            return self.stateOfCharge

        def getAvgBatteryTemp(self):
            return self.avgBatteryTemperature

        def getAvgPackCurrent(self):
            return self.avgPackCurrent

        def getFanSpeed(self):
            return self.fanSpeed

        def decodeMessage1(self, data):
            """Decode CAN message from BMS with ID# 0x001. Message includes Failsafe Statuses, Inst. Pack Voltage,
                Inst. Pack Current, Highest Temperature, Thermistor ID with Highest Temperature"""
            try:
                # failsafe statuses
                self.failsafeStat = (data[1] | data[0])
                self.voltageFailsafeActive = self.failsafeStat & 0x1
                self.currentFailsafeActive = (self.failsafeStat >> 1) & 0x1
                self.relayFailsafeActive = (self.failsafeStat >> 2) & 0x1
                self.cellBalancingActive = (self.failsafeStat >> 3) & 0x1
                self.chargeInterlockFailsafeActive = (self.failsafeStat >> 4) & 0x1
                self.thermistorBValueTableInvalid = (self.failsafeStat >> 5) & 0x1
                self.inputPowerSupplyFailsafeActive = (self.failsafeStat >> 6) & 0x1

                # pack instantaneous voltage
                self.voltage = float(s16(data[2] << 8 | data[3])/10)

                # pack instantaneous current
                self.current = float(s16(data[4] << 8 | data[5])/10)

                # highest temperature
                self.highestTemperature = data[6]

                # id of thermistor with highest temperature
                self.highestTemperatureThermistorID = data[7]

            except:
                print(traceback.format_exc())

        def decodeMessage2(self, data):
            """Decode CAN message from BMS with ID# 0x002. Message includes State of Charge, Average Temperature,
                Average Pack Current. """
            try:
                # state of charge
                self.stateOfCharge = float(data[0]/2)

                # average battery temperature
                self.avgBatteryTemperature = data[1]

                # average pack current
                self.avgPackCurrent = float(s16(data[2] << 8 | data[3])/10)

                # fan speed
                self.fanSpeed = data[4]

            except:
                print(traceback.format_exc())

    class MCU_Control():
        def __init__(self):
            self.msgID = 0x003
            self.speed = 0

        def getSpeed(self):
            return self.speed

        def decodeMessage(self, data):
            """Decode CAN message from MCU. Message includes Speed"""
            try:
                # speed
                self.speed = data[0]
            except:
                print(traceback.format_exc())

    class Blinkers_Control():
        def __init__(self):
            self.msgID = 0x004
            self.rightBlinker = 0
            self.leftBlinker = 0
            self.hazardBlinker = 0

        def getRightBlinker(self):
            return self.rightBlinker

        def getLeftBlinker(self):
            return self.leftBlinker

        def getHazardBlinker(self):
            return self.hazardBlinker

        def decodeMessage(self, data):
            """Decode CAN message from blinker. Message includes status of hazards, right, and left blinker"""
            try:
                # hazard
                self.hazardBlinker = data[0]

                # right
                self.rightBlinker = data[1]

                # left
                self.leftBlinker = data[2]

            except:
                print(traceback.format_exc())

# helper functions
def s16(value):
    """ Converts a 16 bit hex to a signed decimal. """
    return -(value & 0x8000) | (value & 0x7fff)

##if __name__ == '__main__':
##    CAN = CAN_Control()
##    while True:
##        CAN.readMessage()
