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
import RPi.GPIO as GPIO
import serial
import logging
from threading import Thread
from time import sleep


#################
# Text message object
#################
class FonaMessage(object):
    def __init__(self, raw_text_message):
        self.__parse(raw_text_message)

    def __parse(self, raw_text_message):
        # raw_text_message will have two lines. The first is headers, the second the message.
        # Headers are a comma seperated list.
        logging.debug("Raw message: {0}".format(raw_text_message))
        headers = raw_text_message[0].split(",")
        logging.debug("Headers: {0}".format(headers))
        # Response includes '+CMGL: ' before the message number. Strip that part.
        self.__msg_number = headers[0][7:]
        # Get rid of the "+ at the front and " at the end.
        self.__sender_number = headers[2].replace("+", "").replace('\"', '')
        # Date and time are separate. Join them together.
        self.__msg_date = ", ".join(headers[4:])
        # The text message is the second part. Replace carriage returns with carriage return + newline.
        self.__text_message = raw_text_message[1].replace("\r", "\r\n")

    def __str__(self):
        return "Message Number: {0}\r\nSender: {1}\r\nDate: {2}\r\nMessage: {3}\r\n".format(self.__msg_number,
                                                                                            self.__sender_number,
                                                                                            self.__msg_date,
                                                                                            self.__text_message)

    def __repr__(self):
        return "Message Number: {0}\r\nSender: {1}\r\nDate: {2}\r\nMessage: {3}\r\n".format(self.__msg_number,
                                                                                            self.__sender_number,
                                                                                            self.__msg_date,
                                                                                            self.__text_message)

    @property
    def sender_number(self):
        return self.__sender_number

    @property
    def message_number(self):
        return self.__msg_number

    @property
    def message_date(self):
        return self.__msg_date

    @property
    def text_message(self):
        return self.__text_message


#################
# FONA object
#################
class Fona(object):
    def __init__(self, serial_port=None, serial_connection=None):
        """
        Initializer for the Fona class.
        :param serial_port:  Physical port FONA is connected to.
        :param serial_connection: Existing serial connection to use.
        :return:
        """
        logging.debug("FONA: Creating FONA object.")
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
                logging.debug("FONA: Serial connection provided.")
                self.__my_port = serial_connection
            else:
                # Otherwise, make our own.
                logging.debug("FONA: Creating serial connection.")
                self.__my_port = serial.Serial(**serial_settings)
        except FileNotFoundError as err:
            logging.warning("FONA: Supplied port does not exist: {0}".format(serial_port))
            logging.debug("FONA: Error: {0}".format(err.args))
            self.__my_port.close()
        finally:
            logging.debug("FONA: Connection status: {0}".format(self.__my_port.isOpen()))
            self.__connected = self.__my_port.isOpen()

        # GPIO setup is up to the user. We'll warn if it's not done already, but we just care about numbers.
        # if GPIO.getmode() == GPIO.UNKNOWN:
        #    print("Warning: GPIO mode not set. Results unpredictable.")

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
                                        send_message="AT+CMGS",
                                        retrieve_message="AT+CMGR"
                                        )

        # Finally, some commands we're going to do simply because all we care about is text messaging
        self.__status_query(self.__status_commands['AT'])
        self.__set_value(self.__set_commands['text_message_format'], 1)
        self.__set_value(self.__set_commands['ringer'], 1)
        self.__set_value(self.__set_commands['use_local_timestamp'], 1)

    def __status_query(self, cmd):
        """

        :rtype : list
        """
        # print(cmd)
        if self.__connected:
            # logging.debug("FONA: Status query: {0}".format(cmd))
            responses = []
            self.__my_port.write((cmd + "\n").encode("ascii"))
            for line in self.__my_port:
                responses.append(line.decode("ascii"))
            # logging.debug("FONA: Query response: {0}".format(responses))
            return responses
        else:
            raise serial.SerialException("Not connected to FONA. Can't get attribute.")

    def __set_value(self, key, value):
        # print("{0}: {1}".format(key, value))
        if self.__connected:
            responses = []
            self.__my_port.write((key + "=" + str(value) + "\n").encode("ascii"))
            for line in self.__my_port:
                responses.append(line.decode("ascii"))
            return responses
        else:
            raise serial.SerialException("Not connected to FONA. Can't set attribute.")

    def connect(self):
        if not self.__connected:
            try:
                self.__my_port.open()
            finally:
                # Send a newline, then an AT to get things started.
                self.__status_query("\n" + self.__status_commands["AT"])
                self.__connected = self.__my_port.isOpen()

    def disconnect(self):
        if self.__connected:
            try:
                self.__my_port.close()
                self.__connected = self.__my_port.isOpen()
            finally:
                pass

    def keep_alive(self):
        self.__status_query(self.__status_commands['AT'])

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

    def get_current_text_messages(self, include_read=False, leave_unread=False):
        if self.__connected:
            cmd = [self.__text_msg_commands['list_messages'],
                   "="]
            if include_read:
                cmd.append('\"ALL\",')
            else:
                cmd.append('\"REC UNREAD\",')
            cmd.append(str(int(leave_unread)))
            cmd.append("\n")
            raw_messages = self.__status_query("".join(cmd))
            trimmed_messages = []
            for line in raw_messages:
                if not str.startswith(line, "AT+CMGL"):
                    # Don't include lines that are only \r\n.
                    if not str.isspace(line):
                        # Strip off extra \r\n at the end of each line
                        trimmed_messages.append(line.rstrip())

            messages = []
            for i in range(0, int((len(trimmed_messages) - 1)/2)):
                messages.append(FonaMessage(trimmed_messages[2*i:2*i+2]))
            return messages
        else:
            raise serial.SerialException("Not connected to FONA. Can't read text messages.")

    def send_text_message(self, destination_number, message):
        if len(message) > 140:
            logging.warning("Message too long. Aborting.")
            return 0
        command = ["AT+CMGS=\"",    # send message command
                   str(destination_number),     # Destination phone number
                   "\"",            # Close the quote on the number
                   "\n",            # Newline
                   message,         # The actual message
                   "\x1A"]          # A Ctrl-Z to end.

        try:
            return self.__status_query("".join(command))
        except serial.SerialException as err:
            logging.warning(err.args[0])
            return 0


#################
# FONA control thread
#################
class FonaThread (Thread):
    def __init__(self, serial_port, ring_indicator_pin=None, gps_coord_locaiton=None):
        Thread.__init__(self)
        logging.debug("Fona control thread: Initializing.")
        logging.debug("Fona control thread: Using port: {0}".format(serial_port))
        logging.debug("Fona control thread: RI pint: {0}".format(ring_indicator_pin))
        logging.debug("Fona control thread: GPS Coordinates: {0}".format(gps_coord_locaiton))
        self.__fona_port = serial_port
        self.__ring_pin = ring_indicator_pin
        self.__gps_coords = gps_coord_locaiton
        self.__stop = False
        self.__fona = Fona(serial_port=self.__fona_port)
        # Using this as a semaphore for the moment. It's not the best way, but I'll look into that later.
        self.__ser_in_use = False

    def stop(self):
        logging.debug("Fona control thread: Stop called.")
        self.__stop = True

    def __connect_to_fona(self):
        logging.debug("Fona control thread: Connecting to Fona.")
        self.__fona.connect()

    def __get_last_text_message(self):
        logging.debug("Fona control thread: Retrieving messages.")
        # TODO: Change this back to False, False.
        return self.__fona.get_current_text_messages(False, True)

    def __send_response(self, destination_number, message_content):
        logging.debug("Fona control thread: Sending message to {0}.".format(destination_number))
        logging.debug("Fona control thread: Message content: {0}.".format(message_content))
        self.__fona.send_text_message(destination_number, message_content)

    def __ring_callback(self, channel):
        logging.debug("Fona control thread: Callback function called.")
        if not self.__ser_in_use:
            for msg in self.__get_last_text_message():
                # Kind of arbitrary, but allows for a number to be 9 or 10 digits
                # Prevent us from sending a message to auto-texts (like from the carrier)
                if len(msg.sender_number) > 8:
                    self.__send_response(msg.sender_number, self.__gps_coords)
        else:
            sleep(1)

    def __setup_callback(self):
        logging.debug("Fona control thread: Setting up callback function.")
        GPIO.add_event_detect(self.__ring_pin, GPIO.FALLING, callback=self.__ring_callback)
        pass

    def run_tests(self):
        logging.debug("Running general tests.")
        for msg in self.__get_last_text_message():
            print(msg)
            if len(msg.sender_number) > 8:
                print("Would send message to {0}.".format(msg.sender_number))

    def run(self):
        logging.debug("Fona control thread: Starting thread running.")
        try:
            while not self.__stop:
                if not self.__fona.connected:
                    self.__fona.connect()
                self.__ser_in_use = True
                self.__fona.keep_alive()
                self.__ser_in_use = False
                sleep(5)
            logging.debug("Fona control thread: Stop was set.")
        finally:
            self.__fona.disconnect()
        pass


#################
# FONA control thread
#################
class FonaTest (Thread):
    def __init__(self, serial_port, ring_indicator_pin=None, gps_coord_locaiton=None):
        Thread.__init__(self)
        logging.debug("Fona control thread: Initializing.")
        logging.debug("Fona control thread: Using port: {0}".format(serial_port))
        logging.debug("Fona control thread: RI pint: {0}".format(ring_indicator_pin))
        logging.debug("Fona control thread: GPS Coordinates: {0}".format(gps_coord_locaiton))
        self.__fona_port = serial_port
        self.__ring_pin = ring_indicator_pin
        self.__gps_coords = gps_coord_locaiton
        self.__stop = False
        self.__fona = Fona(serial_port=self.__fona_port)
        # Using this as a semaphore for the moment. It's not the best way, but I'll look into that later.
        self.__ser_in_use = False

    def stop(self):
        logging.debug("Fona control thread: Stop called.")
        self.__stop = True

    def __connect_to_fona(self):
        logging.debug("Fona control thread: Connecting to Fona.")
        self.__fona.connect()

    def __ring_callback(self, channel):
        logging.debug("Fona control thread: Callback function called.")
        if not self.__ser_in_use:
            for msg in self.__get_last_text_message():
                # Kind of arbitrary, but allows for a number to be 9 or 10 digits
                # Prevent us from sending a message to auto-texts (like from the carrier)
                if len(msg.sender_number) > 8:
                    logging.debug("We would send {0} to {1}".format(self.__gps_coords, msg.sender_number))
        else:
            sleep(1)

    def __setup_callback(self):
        logging.debug("Fona control thread: Setting up callback function.")
        GPIO.setup(self.__ring_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.__ring_pin, GPIO.FALLING, callback=self.__ring_callback)
        pass

    def run(self):
        logging.debug("Fona control thread: Starting thread running.")
        try:
            self.__setup_callback()
            while not self.__stop:
                if not self.__fona.connected:
                    self.__fona.connect()
                self.__ser_in_use = True
                self.__fona.keep_alive()
                self.__ser_in_use = False
                sleep(5)
            logging.debug("Fona control thread: Stop was set.")
        finally:
            self.__fona.disconnect()
        pass


#################
# Test FONA
#################
def fona_main():
    # Only for testing. Remove later.
    SERIAL_PORT = "/dev/ttyAMA0"
    GPIO.setmode(GPIO.BCM)
    my_fona = Fona(SERIAL_PORT)
    try:
        my_fona.connect()

        # print("ATI: {0}".format(my_fona.ATI))
        # print("Sim Card Number: {0}".format(my_fona.sim_card_number))
        # print("Network Status: {0}".format(my_fona.network_status))
        # print("Ringer: {0}".format(my_fona.ringer))
        # GPIO.cleanup()

        # import datetime
        # msgs = my_fona.get_current_text_messages(include_read=False, leave_unread=True)
        # for msg in msgs:
        #     print(msg)
            # text_response = datetime.datetime.now().isoformat()
            # print(text_response)
            # print(my_fona.send_text_message(destination, text_response))

        my_fona_thread = FonaTest(SERIAL_PORT, ring_indicator_pin=4, gps_coord_locaiton="Fake data.")
        my_fona_thread.start()
        sleep(10)
        my_fona_thread.run_tests()
        my_fona_thread.stop()
        sleep(2)
        GPIO.cleanup()

    except serial.SerialTimeoutException as err:
        print("Error: {0}".format(err))
    except serial.SerialException as err:
        print("Error: {0}".format(err))


if __name__ == "__main__":
    import sys

    debugLevel = logging.DEBUG
    logging.basicConfig(stream=sys.stderr,
                        format='%(asctime)s %(levelname)s:%(message)s',
                        level=debugLevel)
    fona_main()
