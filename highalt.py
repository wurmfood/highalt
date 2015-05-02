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
# logging.basicConfig(filename=os.path.join(rootDir, 'highalt.log'),
#                    format='%(asctime)s %(levelname)s:%(message)s',
#                    level=debugLevel)
# For testing, log to console:
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=debugLevel)

# In case we're on the Pi, start up the camera.
usingCamera = False
if os.name != 'nt':
    logging.info('Enabling camera.')
    import picamera
    usingCamera = True
else:
    logging.info('On Windows, so no camera enabled.')

logging.info('Camera enabled: %s', usingCamera)


# Create the directories we're going to store things in.
def create_data_dirs():
    logging.debug('Creating data directories.')
    # Get today's date and separate out the time and date parts.
    d = datetime.datetime.today()
    # Date format: YYYY-MM-DD
    date_dir = d.strftime('%Y-%m-%d')
    # Time format: 24-hour HH-MM-SS
    time_dir = d.strftime('%H-%M-%S')
    # Create the dirs, root\date\time.
    video_data_dir = os.path.join(rootDir, date_dir, time_dir, 'video')
    sensor_data_dir = os.path.join(rootDir, date_dir, time_dir, 'sensors')
    # Exist ok means that if the dirs already exist, don't freak out.
    os.makedirs(video_data_dir, exist_ok=True)
    os.makedirs(sensor_data_dir, exist_ok=True)
    # Return the paths we just created.
    return video_data_dir, sensor_data_dir

# Create the directories we're going to use.
vDir, sDir = create_data_dirs()
logging.info('Video dir: %s', vDir)
logging.info('Sensor dir: %s', sDir)

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


# Counter to keep track of which subdirectory we're in for the camera
cameraSubDirNum = 0


# Define our camera thread
# if usingCamera:
class CameraThread (threading.Thread):
    def __init__(self, instance_num):
        logging.debug('Creating new camera thread.')
        threading.Thread.__init__(self)
        self.threadPath = os.path.join(vDir, '{:04d}'.format(instance_num))
        logging.info('Creating new directory for video: %s', self.threadPath)
        os.mkdir(self.threadPath)

    def gen_paths(self, file_list):
        tmp_array = []
        for i in file_list:
            tmp_array.append(os.path.join(self.threadPath, i))
        return list(tmp_array)

    def run(self):
        # Start a camera instance
        logging.debug('Camera thread running.')
        try:
            with picamera.PiCamera() as camera:
                logging.debug('Camera instance created. Setting options.')
                # Setup basic options
                camera.vflip = True
                camera.hflip = True
                # 480p
                # camera.resolution = (720, 480)
                # 720p
                camera.resolution = (1280, 720)
                # 1080p
                # camera.resolution = (1920, 1080)
                camera.framerate = 30
                # Record a sequence of videos
                for filename in camera.record_sequence(
                        (self.gen_paths('%08d.h264' % i for i in range(1, 36))),
                        quality=20):
                    logging.debug('Recording to file: %s', filename)
                    camera.wait_recording(600)
        except KeyboardInterrupt:
            logging.warning("Received keyboard interrupt. Shutting down camera thread.")
            global usingCamera
            usingCamera = False
        except:
            logging.warning('Caught an exception. Closing thread.')
            logging.warning('Exception: ', sys.exc_info()[0])


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
            global headers_not_parsed
            while True:
                # Open a file to write data to and write 100 lines.
                line_count = 0
                with open(self.gen_filename(), 'wt', encoding='utf-8') as f:
                    logging.debug('Opened new file for sensor data: %s', f.name)
                    while line_count < 100:
                        # We have to send this to start the data flowing
                        # Also keep writing to it just to make sure the buffer on the other
                        # end stays active.
                        self.ser.write(self.keep_alive)

                        # Take the line we read, strip off end characters and convert it from
                        # a series of bytes into a string.
                        response = self.ser.readline().rstrip().decode()
                        logging.debug(str(line_count) + " : " + response)

                        # In case we haven't already done so, separate out the headers.
                        # We're going to want them for each file. Maybe.
                        if headers_not_parsed and len(response.split(",")) > 1:
                            logging.debug("Don't have headers, trying to parse.")
                            self.get_headers(response, sensor_headers)
                            logging.debug(sensor_headers)
                            logging.debug("Supposedly we got headers.")
                            if len(sensor_headers) > 1:
                                headers_not_parsed = False

                        # If we just opened a new file and we have headers, print them to the file.
                        if line_count == 0 and not headers_not_parsed:
                            logging.debug("We have headers, line count is zero, so writing headers to file.")
                            # Joins the headers using a comma to separate them.
                            f.write(','.join(str(x) for x in sensor_headers))
                            f.write('\n')

                        # Make sure the response actually has data in it
                        if len(response) > 0:
                            logging.debug("Got a response, headers already written, writing line to file.")
                            # Write our response and attach an endline.
                            f.write(response)
                            f.write('\n')
                            f.flush()
                            # We wrote another line, increment the counter.
                            line_count += 1
        except IOError:
            logging.debug("IO Problem. Trying to fix.")
            # try again to open the serial connection
            establish_serial_connection()
            serial_connection.open()
            # Reset the Arduino
            reset_arduino()
        except serial.SerialException:
            logging.debug("Problem with serial connection. Trying to re-start one.")
            # try again to open the serial connection
            establish_serial_connection()
            serial_connection.open()
            # Reset the Arduino
            reset_arduino()
        except KeyboardInterrupt:
            logging.warning('Received keyboard interrupt.')
        except:
            logging.warning('Exception: ', sys.exc_info()[0])
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


# Clear the screen regardless of the OS.
# This will go away once we are storing data better.
# def cls():
#    os.system('cls' if os.name == 'nt' else 'clear')


camThread = None
dataThread = None


# Supervise the threads, recreating if needed
try:
    while True:
        if usingCamera:
            if not camThread or not camThread.is_alive():
                if not camThread:
                    logging.debug('No camera thread.')
                elif not camThread.is_alive():
                    logging.debug('Camera thread exists but not alive')
                camThread = CameraThread(cameraSubDirNum)
                camThread.start()
                cameraSubDirNum += 1
                time.sleep(1)
            elif camThread:
                camThread.join(1)
        else:
            # Camera either isn't connected or wrong OS. Ignore.
            pass

        if serial_connection.isOpen():
            if not dataThread or not dataThread.is_alive():
                dataThread = DataThread()
                dataThread.start()
                time.sleep(1)
            elif dataThread:
                dataThread.join(1)
        else:
            logging.info("No serial connection. Trying to establish.")
            # try again to open the serial connection
            establish_serial_connection()
            serial_connection.open()
            # Reset the Arduino
            reset_arduino()
        # If neither camera nor serial connection is available, abort.
        if not usingCamera and not serial_connection.isOpen():
            logging.info("Nothing connected. Shutting down.")
            logging.shutdown()
            break
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
    if camThread and camThread.is_alive():
        camThread.join()
    logging.shutdown()




