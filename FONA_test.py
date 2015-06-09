#!/usr/bin/env python3

import serial

def send_at(connection):
    message = "AT"
    try:
        connection.writeline(message)
        for line in connection:
            print(line)
    except serial.SerialException as err:
        print(err.args)

def send_ati():
    pass

def check_timestamp_mode():
    command = "AT+CLTS?"
    pass

def set_local_timestamp_mode():
    enable_command = "AT+CLTS=1"
    write_command = "AT&W"
    pass

def get_local_timestamp():
    command = "AT+CCLK?"

def fona_test():
    serial_connection = serial.Serial(port="/dev/ttyUSB0",
                                      baudrate=115200,
                                      bytesize=serial.EIGHTBITS,
                                      parity=serial.PARITY_NONE,
                                      stopbits=serial.STOPBITS_ONE,
                                      timeout=3)
    with serial_connection:
        send_at(serial_connection)
    pass



############################
# Start it all up.
############################
if __name__ == "__main__":
    fona_test()

