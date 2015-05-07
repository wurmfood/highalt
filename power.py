#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO
import os

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
# 22    ----- 330 ohm ---|
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
# pin 22 will go to low.
#
# Note that pin 22 = board pin 15
# Pin 3.3 V = board pin 17
# Pin GND = board pins 25, 20, 14
#
############################

# fake_shutdown_cmd = "shutdown -k now"
real_shutdown_cmd = "shutdown -h --no-wall now"

# Pin to use for power detection
POWERPIN = 22


############################
# Start it all up, alt option.
############################
def main():
    # Setup GPIO pins
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(POWERPIN, GPIO.IN)

    while True:
        # Monitor the pin.
        GPIO.wait_for_edge(POWERPIN,
                           GPIO.FALLING)

        # Require it to still be pushed after 5 seconds.
        time.sleep(5)
        if GPIO.input(POWERPIN) == 0:
            os.system(real_shutdown_cmd)


############################
# Start it all up.
############################
if __name__ == "__main__":
    main()