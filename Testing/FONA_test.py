#!/usr/bin/env python3

import serial
import datetime
import time
import RPi.GPIO as GPIO


message_received = False

def send_message(connection: serial.Serial, message: str):
    # Create our actual message. Strip it of any extra characters
    # then append a newline and encode the whole thing.
    msg = (message.rstrip() + "\n").encode("ascii")
    try:
        connection.write(msg)
        for line in connection:
            print(line.rstrip().decode("ascii"))
    except serial.SerialException as err:
        print(err.args[0])


def send_text_message(connection: serial.Serial, destination, message: str):
    if len(message) > 140:
        print("Message too long. Aborting.")
        return
    command = ["AT+CMGS=\"",    # send message command
               destination,     # Destination phone number
               "\"",            # Close the quote on the number
               "\n",            # Newline
               message,         # The actual message
               "\x1A"]          # A Ctrl-Z to end.

    try:
        connection.write("".join(command).encode("ascii"))

        # Print out the response
        for line in connection:
            print(line.rstrip().decode("ascii"))
    except serial.SerialException as err:
        print(err.args[0])


def get_current_network_time(connection: serial.Serial):
    message = ("AT+CCLK?".rstrip() + "\n").encode("ascii")
    responses = []
    try:
        connection.write(message)
        for line in connection:
            responses.append(line.rstrip().decode("ascii"))
    except serial.SerialException as err:
        print(err.args[0])

    # We only actually want the first response.
    # Responses[0] should be the command back, [1] is the answer, [2] is blank, [3] is OK
    date_and_time = None
    if responses[1][0:7] == "+CCLK: ":
        date_and_time = responses[1][8:len(responses[1])-1]
        print(date_and_time)

    assert isinstance(date_and_time, str)
    return date_and_time


def list_current_messages(connection: serial.Serial, get_all=True, leave_unread=True):
    try:
        # Make sure we're in the correct message format:
        connection.write("AT+CMGF=1\n".encode("ascii"))
        for line in connection:
            # print(line.decode("ascii"))
            # The print was for testing. Now just read the lines and toss them.
            pass

        if get_all:
            msg = "AT+CMGL=\"ALL\"," + str(int(leave_unread)) + "\n"
        else:
            msg = "AT+CMGL=\"REC UNREAD\"," + str(int(leave_unread)) + "\n"
        connection.write(msg.encode("ascii"))
        for line in connection:
            print(line.rstrip().decode("ascii"))
    except serial.SerialException as err:
        print(err.args[0])


def ringer_pin_callback(ringer_pin):
    print("We got a ring!")
    time.sleep(.12)
    global message_received
    message_received = True


def setup_gpio():
    ri_pin = 26
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ri_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(ri_pin, GPIO.FALLING, callback=ringer_pin_callback, bouncetime=200)


def fona_test():
    serial_settings = {"port": "/dev/ttyUSB0",
                       "baudrate": 115200,
                       "bytesize": serial.EIGHTBITS,
                       "parity": serial.PARITY_NONE,
                       "stopbits": serial.STOPBITS_ONE,
                       "timeout": 1}

    test_messages = ["\n",
                     "AT",          # Basic hello
                     # "ATI",         # Get module name and revision
                     # "AT+CMEE=2",   # Turn on verbose errors
                     # "AT+COPS?",    # Are we connected to a network?
                     # "AT+CSQ",      # Signal strength
                     # "AT+CBC",      # Battery state
                     # "AT+CLTS=1",   # Set local timestamp mode
                     # "AT+CLTS?",    # Get timestamp mode
                     # "AT+CCLK?",    # Check the clock
                     # "AT&V",        # All current settings
                     # "AT+CMGF?",    # What message format are we in?
                     # "AT+CMGF=1",   # Change to text format
                     # "AT+CMGL=\"REC UNREAD\",1",
                     # "AT+CMGL=\"ALL\",1",
                     # "AT+CFGRI?",     # Querry the ringer status.
                     # "AT+CFGRI=1",  # RI pin will go low when SMS received
                     # "AT&W"       # Write out our changes
                     # "ATE1"          # Echo on/off - 0 = no echo
                     ]
    try:
        serial_connection = serial.Serial(**serial_settings)
        with serial_connection:
            for msg in test_messages:
                send_message(serial_connection, msg)

            my_number = "4158284862"
            txt_message = str(datetime.datetime.isoformat(datetime.datetime.now()))
            # send_text_message(serial_connection, my_number, txt_message)

            get_current_network_time(serial_connection)

            list_current_messages(serial_connection, leave_unread=False)

            setup_gpio()

            while not message_received:
                time.sleep(1)

    except serial.SerialException as err:
        print(err.args[0])
    finally:
        GPIO.cleanup()
        pass


############################
# Start it all up.
############################
if __name__ == "__main__":
    fona_test()
