#!/usr/bin/env python3

import os
import datetime
import logging
from time import sleep
from HighaltHardware.HighaltArduino import ArduinoThreadSupervisor
from HighaltHardware.AdafruitFONA import FonaThread


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


if __name__ == "__main__":
    # Set our root directory
    rootDir = 'E:\\David\\highalt' if os.name == 'nt' else '/data/highalt'

    # Setup our logging. We want to do this early so we can cover everything.
    # Debug level options:
    # DEBUG
    # INFO
    # WARNING
    # ERROR
    # CRITICAL
    debugLevel = logging.INFO
    logging.basicConfig(filename=os.path.join(rootDir, 'highalt.log'),
                        format='%(asctime)s %(levelname)s:%(message)s',
                        level=debugLevel)

    # Create the directories we're going to use.
    vDir, sDir = create_data_dirs()
    logging.info('Video dir: {0}'.format(vDir))
    logging.info('Sensor dir: {0}'.format(sDir))

    #################################
    # Camera Thread section
    #################################

    # In case we're on the Pi, start up the camera.
    usingCamera = False
    arch = os.uname()[4]
    op_sys = os.uname()[0]
    logging.info("Architecture: {0}".format(arch))
    logging.info("OS Name: {0}".format(op_sys))
    if arch == 'armv7l':
        from HighaltHardware.HighaltCamera import CamThreadSupervisor
        logging.info('Enabling camera.')
        usingCamera = True
    else:
        logging.info('On Windows, so no camera enabled.')

    logging.info('Camera enabled: {0}'.format(usingCamera))

    ################################
    # Serial Ports
    ################################
    arduino_port = 'COM3' if op_sys == 'nt' else '/dev/ttyUSB0'
    fona_port = '/dev/ttyACM0' if arch == 'armv7l' else None

    ################################
    # Establish and control the threads we've set up
    ################################

    ArduinoSupThread = None
    CamSupThread = None
    FonaSupervisor = None

    # Supervise the threads, recreating if needed
    stop = False
    try:
        logging.info("Starting Arduino thread.")
        ArduinoSupThread = ArduinoThreadSupervisor(arduino_port, sDir)
        ArduinoSupThread.start()
        sleep(1)
        if usingCamera:
            logging.info("Starting Camera thread.")
            CamSupThread = CamThreadSupervisor(vDir, 600, 30)
            # CamSupThread.start()
        if fona_port:
            logging.info("Starting Fona thread.")
            FonaSupervisor = FonaThread(fona_port, 4, ArduinoSupThread.current_gps_coords)
            FonaSupervisor.start()
        while not stop:
            if usingCamera:
                # CamSupThread.join(5)
                pass
            if fona_port:
                FonaSupervisor.join(5)
            ArduinoSupThread.join(5)

    except KeyboardInterrupt:
        logging.warning("Received keyboard interrupt. Shutting down.")
        stop = True
        ArduinoSupThread.stop()
        FonaSupervisor.stop()
        CamSupThread.stop()
    except NameError as err:
        logging.warning("Thread Control - Name Error:")
        logging.warning(err.args)
    # except AttributeError as err:
    #    logging.warning("Thread Control - Attribute Error:")
    #    for i in err.args:
    #        logging.warning(i)
    finally:
        logging.shutdown()
