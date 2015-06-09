#!/usr/bin/env python3

import Serial

def send_at(connection):
    message = "AT"
    try:
        connection.writeline(message)
        for line in connection:
            print(line)
    except Serial.SerialException as err:
        print(err.args)

def send_ati():
    pass

def check_timestamp_mode():
    pass

def set_local_timestamp_mode():
    pass

def fona_test():
    serial_connection = Serial.Serial(port="/dev/ttyUSB0",
                                      baudrate=115200,
                                      bytesize=Serial.EIGHTBITS,
                                      parity=Serial.PARITY_NONE,
                                      stopbits=Serial.STOPBITS_ONE,
                                      timeout=3)
    with serial_connection:
        send_at(serial_connection)
    pass



############################
# Start it all up.
############################
if __name__ == "__main__":
    fona_test()

