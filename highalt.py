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
logging.basicConfig(filename=os.path.join(rootDir, 'highalt.log'),
                    format='%(asctime)s %(levelname)s:%(message)s',
                    level=debugLevel)


# In case we're on the Pi, start up the camera.
usingCamera = False
if os.name != 'nt':
    logging.info('Enabling camera.')
    import picamera
    usingCamera = True
else:
    logging.info('On Windows, so no camera enabled.')


def create_data_dirs():
    logging.debug('Creating data directories.')
    d = datetime.datetime.today()
    date_dir = d.strftime('%Y-%m-%d')
    time_dir = d.strftime('%H-%M-%S')
    video_data_dir = os.path.join(rootDir, date_dir, time_dir, 'video')
    sensor_data_dir = os.path.join(rootDir, date_dir, time_dir, 'sensors')
    os.makedirs(video_data_dir, exist_ok=True)
    os.makedirs(sensor_data_dir, exist_ok=True)
    return video_data_dir, sensor_data_dir

# Create the directories we're going to use.
vDir, sDir = create_data_dirs()
logging.info('Video dir: %s', vDir)
logging.info('Sensor dir: %s', sDir)

# Automatically select the correct port for the OS.
port = 'COM3' if os.name == 'nt' else '/dev/ttyACM0'
logging.debug('Setting up connection on %s', port)
serial_connection = serial.Serial(port,
                                  baudrate=115200,
                                  stopbits=serial.STOPBITS_ONE,
                                  bytesize=serial.EIGHTBITS,
                                  parity=serial.PARITY_NONE,
                                  timeout=1
                                  )
# Store the headers we get from the Arduino
sensor_headers = []
# Have we parsed the headers already?
headers_not_parsed = True

logging.debug('Resetting connection.')
# Reset the Arduino by toggling DTR
serial_connection.setDTR(True)
time.sleep(1)
serial_connection.setDTR(False)
# Flush any data there at the moment
serial_connection.flushInput()
serial_connection.flushOutput()


def get_headers(to_parse, h):
    # Separate out the headers so we can include them in future files
    x = to_parse.split(",")
    for l in x:
        h.append(l)
    logging.debug('Parsing headers.')
    logging.debug('Before: %s', to_parse)
    logging.debug('After: %s', h)

cameraSubDirNum = 0

if usingCamera:
    class CameraThread (threading.Thread):
        def __init__(self, instance_num):
            threading.Thread.__init__(self)
            self.threadPath = os.path.join(vDir, '{:04d}'.format(instance_num))
            logging.info('Creating new directory for video: %s', self.threadPath)
            os.mkdir(self.threadPath)

        def run(self):
            # Start a camera instance
            logging.debug('Starting new camera thread.')
            try:
                with picamera.PiCamera() as camera:
                    logging.debug('Camera instance created. Setting options.')
                    # Setup basic options
                    camera.vflip = True
                    camera.hflip = True
                    camera.resolution = (720, 480)
                    camera.framerate = 30
                    # Record a sequence of videos
                    for filename in camera.record_sequence(
                            (os.path.join(self.threadPath, '08d.h264') % i for i in range(1, 36)),
                            quality=20):
                        logging.debug('Recording to file: %s', filename)
                        camera.wait_recording(600)
            except:
                logging.warning('Caught an exception. Closing thread.')


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
                            get_headers(response, sensor_headers)
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


# Clear the screen regardless of the OS.
# This will go away once we are storing data better.
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


if usingCamera:
    camThread = None
dataThread = None


# Supervise the threads, recreating if needed
try:
    while True:
        if usingCamera:
            if not camThread or not camThread.is_alive():
                camThread = CameraThread(cameraSubDirNum)
                camThread.start()
                cameraSubDirNum += 1
                time.sleep(1)
            elif camThread:
                camThread.join(1)
        if not dataThread or not dataThread.is_alive():
            dataThread = DataThread()
            dataThread.start()
            time.sleep(1)
        elif dataThread:
            dataThread.join(1)
except:
    logging.warning('Exception: ', sys.exc_info()[0])
finally:
    logging.info('Closing serial connection')
    serial_connection.close()


