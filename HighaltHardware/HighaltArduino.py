#!/usr/bin/env python3

##############################
# Data Thread section
##############################

import logging
import os
from time import sleep
from threading import Thread
from datetime import datetime
from serial import Serial, SerialException, SerialTimeoutException, STOPBITS_ONE, EIGHTBITS, PARITY_NONE


# Define our data thread.
class ArduinoDataThread (Thread):
    def __init__(self, serial_connection, output_directory, headers):
        Thread.__init__(self)
        self.__ser = serial_connection
        self.__out = output_directory
        self.headers = headers
        self.headers_parsed = False
        # Keep alive, basically.
        # Have to encode it because the serial stream only takes bytes.
        self.__keep_alive = "Hello.".encode('ascii')
        self.last_received_line = None
        self.__stop = False
        logging.debug('Data Thread: New logging thread created.')

    def run(self):
        try:
            # If we haven't been told to shut down:
            while not self.__stop:
                # Open a file to write data to and write 100 lines.
                line_count = 0
                with open(self.gen_filename(), 'wt', encoding='utf-8') as f:
                    logging.debug('Data Thread: Opened new file for sensor data: {0}'.format(f.name))
                    while line_count < 100:
                        # We have to send this to start the data flowing
                        # Also keep writing to it just to make sure the buffer on the other
                        # end stays active.
                        self.__ser.write(self.__keep_alive)

                        # Take the line we read, strip off end characters and convert it from
                        # a series of bytes into a string.
                        response = self.__ser.readline().rstrip().decode()
                        logging.debug(str(line_count) + " : " + response)

                        # In case we haven't already done so, separate out the headers.
                        # We're going to want them for each file. Maybe.
                        if not self.headers_parsed and len(response.split(",")) > 1:
                            logging.debug("Data Thread: Don't have headers, trying to parse.")
                            self.get_headers(response)
                            logging.debug(self.headers)
                            logging.debug("Data Thread: Supposedly we got headers.")
                            if len(self.headers) > 1:
                                self.headers_parsed = True

                        # If we just opened a new file and we have headers, print them to the file.
                        if line_count == 0 and self.headers_parsed:
                            logging.debug("Data Thread: We have headers, line count is zero. Writing headers to file.")
                            # Joins the headers using a comma to separate them.
                            f.write(','.join(str(x) for x in self.headers))
                            f.write('\n')

                        # Make sure the response actually has data in it
                        if len(response) > 0:
                            logging.debug("Data Thread: Writing response to file.")
                            # Write our response and attach an endline.
                            self.last_received_line = response
                            f.write(response)
                            f.write('\n')
                            f.flush()
                            # We wrote another line, increment the counter.
                            line_count += 1

                        if self.__stop:
                            break
        except SerialException or SerialTimeoutException as err:
            logging.debug("Data Thread: Problem with serial connection. Trying to re-start one.")
            logging.debug("Error: {0}".format(err.args))
            logging.debug("Exiting thread.")

    # A small function to generate the name of the file we'll log to.
    # Format for the filename is: YYYYMMDD.HHMMSS.csv
    def gen_filename(self):
        d = datetime.today()
        fn = os.path.join(self.__out, d.strftime('%Y%m%d') + "." + d.strftime('%H%M%S') + ".csv")
        assert isinstance(fn, str)
        return fn

    def get_headers(self, to_parse):
        # Separate out the headers so we can include them in future files
        x = to_parse.split(",")
        for l in x:
            self.headers.append(l)
        logging.debug('Data Thread: Parsing headers.')
        logging.debug('Data Thread: Before: {0}'.format(to_parse))
        logging.debug('Data Thread: After: {0}'.format(self.headers))


class ArduinoThreadSupervisor (Thread):
    def __init__(self, port, output_dir):
        Thread.__init__(self)
        self.__serial_connection = Serial()
        # Place to store headers
        self.sensor_headers = []
        # Have we parsed the headers already?
        self.headers_parsed = False
        self.__port = port
        self.__out_dir = output_dir
        self.__current_thread = None
        self.__stop = False

    def stop(self):
        self.__stop = True

    def last_line(self):
        return self.__current_thread.last_received_line

    # If we have a connection, reset the Arduino by toggling DTR
    def __reset_arduino(self):
        if self.__serial_connection.isOpen():
            logging.debug('Arduino Supervisor: Resetting connection to Arduino.')
            self.__serial_connection.setDTR(True)
            sleep(1)
            self.__serial_connection.setDTR(False)
            # Flush any data there at the moment
            self.__serial_connection.flushInput()
            self.__serial_connection.flushOutput()

    # Define a function to actually establish a connection. That way, if we don't
    # get one immediately, we can try to get one any time we would try to establish
    # a new thread.
    def __setup_serial_connection(self):
        try:
            logging.debug('Arduino Supervisor: Setting up connection on {0}'.format(self.__port))
            self.__serial_connection.port = self.__port
            self.__serial_connection.baudrate = 115200
            self.__serial_connection.stopbits = STOPBITS_ONE
            self.__serial_connection.bytesize = EIGHTBITS
            self.__serial_connection.parity = PARITY_NONE
            self.__serial_connection.timeout = 2
        except SerialException as err:
            logging.warning("Arduino Supervisor: Serial Error: {0}".format(err))

    def run(self):
        # Try to establish a connection to the Arduino
        self.__setup_serial_connection()
        # So long as we're not told to stop
        while not self.__stop:
            try:
                self.__serial_connection.open()
                if self.__serial_connection.isOpen():
                    logging.debug("Arduino Supervisor: Connection open.")
                    # Reset the Arduino:
                    self.__reset_arduino()
                    # Set up a data thread:
                    self.__current_thread = ArduinoDataThread(self.__serial_connection,
                                                              self.__out_dir,
                                                              self.sensor_headers)
                    # Start the thread
                    self.__current_thread.start()
                    # Join
                    self.__current_thread.join()
                else:
                    logging.debug("Arduino Supervisor: Connection failed to open.")
            except KeyboardInterrupt:
                logging.warning('Arduino Supervisor: Received keyboard interrupt.')
                self.__stop = True
            finally:
                logging.info("Arduino Supervisor: Closing the serial connection before exiting.")
                self.__serial_connection.close()


if __name__ == "__main__":
    import getopt
    import sys

    debugLevel = logging.DEBUG
    logging.basicConfig(stream=sys.stderr,
                        format='%(asctime)s %(levelname)s:%(message)s',
                        level=debugLevel)

    def process_args(inargs):
        # Automatically select the correct port for the OS.
        out = os.getcwd()
        port = 'COM3' if os.name == 'nt' else '/dev/ttyACM0'
        usage = """
        -o, --outDir    Where to output the videos.
        -p, --port      The port to connect to the Arduino on.
        """

        try:
            # allow -o or --outDir, -t or --time, -n or --num, and -h.
            opts, args = getopt.getopt(inargs, "ho:p:", ["outDir", "port"])

        except getopt.GetoptError as err:
            print(err.msg)
            print("\n")
            print(usage)
            sys.exit(2)

        for opt, arg in opts:
            if opt == "-h":
                print(usage)
            elif opt == "-p":
                port = arg
                print("{0} is where we'll look for the Arduino.".format(arg))
            elif opt == "-o":
                out = arg
                print('Output Dir: {0}'.format(arg))
            elif opt == "-":
                # We don't actually detect this, but sending a - on its own kills further
                # processing. Not sure why. Will find out later.
                print("What?")
            else:
                print("Unrecognized option: {0}:{1}".format(opt, arg))

        return out, port

    out_dir, serial_port = process_args(sys.argv[1:])
    sup = ArduinoThreadSupervisor(serial_port, out_dir)
    sup.start()
    sleep(1)
    sup.stop()
