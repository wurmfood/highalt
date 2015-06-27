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
# While I wanted to do something more comprehensive, I'm just doing the text messaging part for now.
#
#####################################################################

#################
# Includes
#################
try:
    import RPi.GPIO as GPIO
except:
    pass
import serial


#################
# Text message object
#################
class Fona_message(object):
    def __init__(self, raw_text_message):
        self.__sender_number, self.__text_message = self.__parse(raw_text_message)

    @staticmethod
    def __parse(self, raw_text_message):
        # These are fake numbers for the moment. TODO: Get the real numbers in here.
        return raw_text_message[0:8], raw_text_message[9:]

    @property
    def sender_number(self):
        return self.__sender_number

    @property
    def text_message(self):
        return self.__text_message

#################
# FONA object
#################
class Fona(object):
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
        if GPIO and GPIO.getmode() == GPIO.UNKNOWN:
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
                                   )

        self.__text_msg_commands = dict(list_messages="AT+CMGL",
                                        delete_message="",
                                        send_message="AT+CMGS"
                                        )

        # Finally, some commands we're going to do simply because all we care about is text messaging
        self.__status_query(self.__status_commands['AT '])
        self.__set_value(self.__text_msg_commands['text_message_format'], 1)
        self.__set_value(self.__set_commands['ringer'], 1)
        self.__set_value(self.__set_commands['use_local_timestamp'], 1)

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
            raise serial.SerialException("Not connected to FONA. Can't get attribute.")

    def __set_value(self, key, value):
        if self.__connected:
            responses = []
            self.__my_port.write((key + "=" + value).encode("ascii"))
            for line in self.__my_port:
                responses.append(line.decode("ascii"))
            return responses
        else:
            raise serial.SerialException("Not connected to FONA. Can't set attribute.")

    def connect(self):
        if not self.__connected:
            try:
                self.__my_port.open()
                # Send a newline, then an AT to get things started.
                self.__status_query("\n" + self.__status_commands["AT"])
                self.__connected = True
            finally:
                pass

    # A neat way to handle getting attributes. It lets the user query the card for information
    # without having to provide an explicit function. Of course, this only works if I've already
    # defined the command needed.
    def __getattr__(self, item):
        if item in self.__status_commands:
            return self.__status_query(self.__status_commands[item])
        elif item in self.__set_commands:
            return self.__status_query(self.__set_commands[item] + "?")
        else:
            classname = self.__class__.__name__
            raise AttributeError("'{classname}' object has no "
                                 "attribute '{item}'".format(**locals()))

    @property
    def connected(self):
        return self.__connected

    def list_current_text_messages(self, include_read=False, leave_unread=False):
        if self.__connected:
            msg = [self.__text_msg_commands['list_messages'],
                   "="]
            if include_read:
                msg.append('\"ALL\",')
            else:
                msg.append('\"REC UNREAD\",')
            msg.append(str(int(leave_unread)))
            msg.append("\n")
            return self.__status_query("".join(msg).encode("ascii"))
        else:
            raise serial.SerialException("Not connected to FONA. Can't read text messages.")

    def send_text_message(self, destination_number, message):
        if len(message) > 140:
            print("Message too long. Aborting.")
            return 0
        command = ["AT+CMGS=\"",    # send message command
                   destination_number,     # Destination phone number
                   "\"",            # Close the quote on the number
                   "\n",            # Newline
                   message,         # The actual message
                   "\x1A"]          # A Ctrl-Z to end.

        try:
            self.__my_port.write("".join(command).encode("ascii"))

            # Print out the response
            response = []
            for line in self.__my_port:
                response.append(line.rstrip().decode("ascii"))
            return response
        except serial.SerialException as err:
            print(err.args[0])
            return 0

    def set_callback_on_pin(self, callback_function, pin):
        """
        Setup a callback using a named pin.

        Setup a callback on one of the following pins: key, power_status, network_status, reset, or ring_indicator.

        :param callback_function:
        :param pin:
        :return:
        """
        pass


#################
# Test FONA
#################

# Only for testing. Remove later.
SERIAL_PORT = "/dev/ttyUSB0"
if GPIO:
    GPIO.setmode(GPIO.BCM)
my_fona = Fona(SERIAL_PORT)
my_fona.connect()

print(my_fona.AT)
print(my_fona.ATI)
print(my_fona.sim_card_number)
print(my_fona.network_status)
print(my_fona.ringer)
print(my_fona.set_fona_option("error_verbosity", str(2)))
print(my_fona.list_current_text_messages())
# GPIO.cleanup()
print(my_fona.send_text_message(4158284862, "This is a test message."))
print(my_fona.list_current_text_messages(include_read=True, leave_unread=True))