#!/usr/bin/env python3

#####################################################################
#
# Module to support the Adafruit FONA vi Python for the Raspberry Pi.
#
# This assumes there is a USB->Serial cable being used. If going directly to the FONA using the
# Pi's serial pins, adjust in pin connections accordingly.
#
# Notes:
#   PS pin is in input mode. Should use a resistor to force it up or down to start.
#   For reset and key pins,  you need additional hardware to do anything useful.
#
#####################################################################

#################
# Includes
#################
import RPi.GPIO as GPIO
import serial


#################
# Pin Connections
#################
# Can use with a tie to ground option to turn the FONA on and off.
# KEY_PIN = 5

# Power Status: LOW = Off, HIGH = Power on
# PS_PIN = 6

# Network Status: 64 ms on, 800 off = running, no connection to network
# 65 ms on, 3 seconds off = Made contact, can send/receive
# 64 ms on, 300 ms off = GPRS data requested is available
# NS_PIN = 13

# Reset Pin: Pull low for 100 ms to reset
# RESET_PIN = 19

# High default, goes low for 120 ms when call received
# RI_PIN = 26


#################
# FONA object
#################
class Fona:
    def __init__(self, serial_port=None, serial_connection=None, key_pin=None, power_status_pin=None,
                 network_status_pin=None, reset_pin=None, ring_indicator_pin=None):
        """
        Initializer for the Fona class.
        :param serial_port:  Physical port FONA is connected to.
        :param serial_connection: Existing serial connection to use.
        :param key_pin: Pin the Key pin is connected to.
        :param power_status_pin: Pin the Power Status (PS) pin is connected to.
        :param network_status_pin: Pin the Network Status (NS) pin is connected to.
        :param reset_pin: Pin the Reset pin is connected to.
        :param ring_indicator_pin: Pin the Ring Indicator (RI) pin is connected to.
        :return:
        """
        # Setup the serial connection
        serial_settings = {"port": serial_port,
                           "baudrate": 115200,
                           "bytesize": serial.EIGHTBITS,
                           "parity": serial.PARITY_NONE,
                           "stopbits": serial.STOPBITS_ONE,
                           "timeout": 1}
        try:
            # If we are handed an existing serial connection, take it.
            if serial_connection:
                self.__my_port = serial_connection
            else:
                # Otherwise, make our own.
                self.__my_port = serial.Serial(**serial_settings)
        finally:
            self.__connected = self.__my_port.isOpen()

        # GPIO setup is up to the user. We'll warn if it's not done already, but we just care about numbers.
        if GPIO.getmode() == GPIO.UNKNOWN:
            print("Warning: GPIO mode not set. Results unpredictable.")

        # Create a set of used pins
        self.__pins = {"key": key_pin,
                       "power_status": power_status_pin,
                       "network_status": network_status_pin,
                       "reset": reset_pin,
                       "ring_indicator": ring_indicator_pin}

        self.__status_commands = dict(AT="AT",
                                      ATI="ATI",
                                      sim_card_number="AT+CCID",
                                      network_status="AT+COPS?",
                                      signal_strength="AT+CSQ",
                                      battery_state="AT+CBC",
                                      network_clock="AT+CCLK?",
                                      current_settings="AT&V"
                                      )

        self.__set_commands = dict(text_message_format="AT+CMGF",
                                   error_verbosity="AT+CMEE",
                                   use_local_timestamp="AT+CLTS",
                                   ringer="AT+CFGRI",
                                   echo="ATE"
                                   )

        self.__text_msg_commands = dict(list_messages="AT+CMGL",
                                        delete_message="",
                                        send_message="AT+CMGS"
                                        )

    def __status_query(self, cmd):
        """

        :rtype : list
        """
        if self.__connected:
            responses = []
            self.__my_port.write((cmd + "\n").encode("ascii"))
            for line in self.__my_port:
                responses.append(line.decode("ascii"))
            return responses
        else:
            return None

    def connect(self):
        if not self.__connected:
            try:
                self.__my_port.open()
                # Send a newline, then an AT to get things started.
                self.__status_query("\n" + self.__status_commands["AT"])
                self.__connected = True
            finally:
                pass

    def __getattr__(self, item):
        if item in self.__status_commands:
            return self.__status_query(self.__status_commands[item])
        elif item in self.__set_commands:
            return self.__status_query(self.__set_commands[item]+"?")
        else:
            classname = self.__class__.__name__
            raise AttributeError("'{classname}' object has no "
                                 "attribute '{item}'".format(**locals()))

    @property
    def connected(self):
        return self.__connected

    @property
    def module_name(self):
        return self.__status_query(self.__status_commands["ATI"])

    @property
    def network_status(self):
        return self.__status_query(self.__status_commands["network_status"])

    @property
    def signal_strength(self):
        return self.__status_query(self.__status_commands["signal_strength"])

    @property
    def battery_state(self):
        return self.__status_query(self.__status_commands["battery_state"])


#################
# Test FONA
#################

# Only for testing. Remove later.
SERIAL_PORT = "/dev/ttyUSB0"

my_fona = Fona(SERIAL_PORT)
my_fona.connect()

print(my_fona.AT)
print(my_fona.ATI)
print(my_fona.sim_card_number)
print(my_fona.module_name)
print(my_fona.network_status)
print(my_fona.ringer)
print(my_fona.echo)
