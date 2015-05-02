#!/usr/bin/env python3

import serial
import time
import os
import datetime
import threading
import logging
import sys

# Set our root directory
rootDir = 'E:\\David\\highalt' if os.name == 'nt' else '/data/highalt'

# Setup our logging. We want to do this early so we can cover everything.
# Debug level options:
# DEBUG
# INFO
# WARNING
# ERROR
# CRITICAL
debugLevel = logging.DEBUG
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=debugLevel)

# Automatically select the correct port for the OS.
port = 'COM3' if os.name == 'nt' else '/dev/ttyACM0'
logging.debug('Setting up connection on %s', port)

# Do this in a way that works better with error checking.
# This way we can just not use the data part if we don't have a serial connection.
serial_connection = serial.Serial()


# I don't like this, but it's more robust if we do it.
# Define a function to actually establish a connection. That way, if we don't
# get one immediately, we can try to get one any time we would try to establish
# a new thread.
def establish_serial_connection():
    try:
        global serial_connection
        serial_connection.port = port
        serial_connection.baudrate = 115200
        serial_connection.stopbits = serial.STOPBITS_ONE
        serial_connection.bytesize = serial.EIGHTBITS
        serial_connection.parity = serial.PARITY_NONE
        serial_connection.timeout = 1
        logging.debug("Serial connection: {0}", serial_connection.isOpen())
    except serial.SerialException as errn:
        logging.warning("Serial Error: {0}".format(errn))


# Store the headers we get from the Arduino
sensor_headers = []
# Have we parsed the headers already?
headers_not_parsed = True


# If we have a connection, reset the Arduino by toggling DTR
def reset_arduino():
    if serial_connection.isOpen():
        logging.debug('Resetting connection.')
        serial_connection.setDTR(True)
        time.sleep(1)
        serial_connection.setDTR(False)
        # Flush any data there at the moment
        serial_connection.flushInput()
        serial_connection.flushOutput()


# Define our data thread.
class DataThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        global serial_connection
        self.ser = serial_connection
        # Keep alive, basically.
        # Have to encode it because the serial stream only takes bytes.
        self.keep_alive = "Hello.".encode('ascii')
        logging.debug('New logging thread created.')

    def run(self):
        # Time to actually connect the serial port and try to communicate.
        try:
            # Pull this in here so it's only done once.
            while True:
                # Open a file to write data to and write 100 lines.
                line_count = 0
                while line_count < 100:
                    # We have to send this to start the data flowing
                    # Also keep writing to it just to make sure the buffer on the other
                    # end stays active.
                    self.ser.write(self.keep_alive)

                    # Take the line we read, strip off end characters and convert it from
                    # a series of bytes into a string.
                    response = self.ser.readline().rstrip().decode()
                    logging.debug(str(line_count) + " : " + response)
        except IOError:
            logging.debug("IO Problem. Trying to fix.")
            # try again to open the serial connection
            establish_serial_connection()
            # Reset the Arduino
            reset_arduino()
        except serial.SerialException:
            logging.debug("Problem with serial connection. Trying to re-start one.")
            # try again to open the serial connection
            establish_serial_connection()
            # Reset the Arduino
            reset_arduino()
        except KeyboardInterrupt:
            logging.warning('Received keyboard interrupt.')
        except:
            logging.warning('Exception: {0}', sys.exc_info()[0])
            logging.warning('Caught an exception. Closing thread.')
        else:
            pass

    # A small function to generate the name of the file we'll log to.
    # Format for the filename is: YYYYMMDD.HHMMSS.csv
    @staticmethod
    def gen_filename():
        d = datetime.datetime.today()
        fn = os.path.join(sDir, d.strftime('%Y%m%d') + "." + d.strftime('%H%M%S') + ".csv")
        assert isinstance(fn, str)
        return fn

    @staticmethod
    def get_headers(to_parse, h):
        # Separate out the headers so we can include them in future files
        x = to_parse.split(",")
        for l in x:
            h.append(l)
        logging.debug('Parsing headers.')
        logging.debug('Before: %s', to_parse)
        logging.debug('After: %s', h)


dataThread = None


# Get the serial connection started, hopefully.
establish_serial_connection()
reset_arduino()

# Supervise the threads, recreating if needed
try:
    while True:
        if not dataThread or not dataThread.is_alive():
            dataThread = DataThread()
            dataThread.start()
            time.sleep(1)
        elif dataThread:
            dataThread.join(1)
except KeyboardInterrupt:
    logging.warning("Received keyboard interrupt. Shutting down.")
except:
    logging.warning('Exception: ', sys.exc_info()[0])
finally:
    logging.info("Shutting down. Joining threads.")
    if dataThread and dataThread.is_alive():
        dataThread.join()
        logging.info('Closing serial connection')
        serial_connection.close()
    logging.shutdown()




