#!/usr/bin/env python3

import serial
import datetime


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
    cmd = "AT+CMGS=\"".encode("ascii")
    dest = destination.encode("ascii")
    close_quote = "\"".encode("ascii")
    newline = b"\n"
    msg = message.encode("ascii")
    ctrl_z = b"\x1A"
    try:
        connection.write(cmd)
        connection.write(dest)
        connection.write(close_quote)
        connection.write(newline)
        connection.write(msg)
        connection.write(ctrl_z)

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
    if responses[1][0:7] == "+CCLK: ":
        print(responses[1][8:len(responses[1])-1])
        pass


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
            send_text_message(serial_connection, my_number, txt_message)

            get_current_network_time(serial_connection)

            list_current_messages(serial_connection, leave_unread=False)

    except serial.SerialException as err:
        print(err.args[0])


############################
# Start it all up.
############################
if __name__ == "__main__":
    fona_test()
