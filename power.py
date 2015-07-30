#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO
import os
import logging

############################
# power.py
#
# Monitor GPIO pins for a change in voltage. On detection, call shutdown.
#
# Some inspiration taken from here:
# http://iot-projects.com/index.php?id=raspberry-pi-shutdown-button
#
# Callback function for GPIO pins demonstrated here:
# http://makezine.com/projects/tutorial-raspberry-pi-gpio-pins-and-python/
#
# For this to work, connect the following:
#
# 17    ----- 330 ohm ---|
#                        |
# 3.3 V ------ 10k ohm --|
#                        |
#                         \ button
#                        |
#                        |
# GND   -----------------|
#
# Normally, the 3.3 V will keep pin 25 high. However,
# on pushing the button, the 3.3 V will go to ground and
# pin 4 will go to low.
#
# Note that pin 17 = board pin 15?
# Pin 3.3 V = board pin 17
# Pin GND = board pins 25, 20, 14
#
############################

# fake_shutdown_cmd = "shutdown -k now"
real_shutdown_cmd = "shutdown -h now"

# Pin to use for power detection
POWERPIN = 17


############################
# Start it all up, alt option.
############################
def main():
    # Setup GPIO pins
    logging.info("Power service started. Setting up monitoring.")
    GPIO.setmode(GPIO.BCM)
    logging.debug("Pin: {0}".format(POWERPIN))
    GPIO.setup(POWERPIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    logging.debug("Pin state: {0}".format(GPIO.input(POWERPIN)))

    while True:
        # Monitor the pin.
        logging.debug("Monitoring the pin.")
        GPIO.wait_for_edge(POWERPIN,
                           GPIO.FALLING)
        logging.info("Power button pushed. Checking again in 5 sec.")
        logging.debug("Edge falling detected.")

        # Require it to still be pushed after 5 seconds.
        time.sleep(5)
        if GPIO.input(POWERPIN) == 0:
            logging.info("Pin still down after 5 min. Initiating shutdown.")
            os.system(real_shutdown_cmd)
        else:
            logging.info("Button was released. Resetting.")


############################
# Start it all up.
############################
if __name__ == "__main__":
    # Setup logging
    debugLevel = logging.INFO
    logging.basicConfig(filename='/var/log/power.log',
                        format='%(asctime)s %(levelname)s: %(message)s',
                        level=debugLevel)

    main()
