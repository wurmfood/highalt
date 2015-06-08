#####################################################################
#
# Module to support the Adafruit FONA vi Python for the Raspberry Pi.
#
# This assumes there is a USB->Serial cable being used. If going directly to the FONA using the
# Pi's serial pins, adjust in pin connections accordingly.
#
# Notes:
#   PS pin is in input mode. Should use a resistor to force it up or down to start.
#   For reset and key pins,  you need additional hardware to do anything useful.
#
#####################################################################

#################
# Includes
#################
import RPi.GPIO as GPIO
import serial



#################
# Pin Connections
#################
KEY_PIN = 5     # Can use with a tie to ground option to turn the FONA on and off.
PS_PIN = 6      # Power Status: LOW = Off, HIGH = Power on

# Network Status: 64 ms on, 800 off = running, no connection to network
# 65 ms on, 3 seconds off = Made contact, can send/receive
# 64 ms on, 300 ms off = GPRS data requested is available
NS_PIN = 13

# Reset Pin: Pull low for 100 ms to reset
RESET_PIN = 19
RI_PIN = 26     # High default, goes low for 120 ms when call received


#################
# AT Commands
#################
# Basic hello command
COMMAND_AT = "AT"

# Get module name and revision
COMMAND_ATI = "ATI"

# Turn on verbose errors
AT_VERBOSE_ERRORS = "AT+CMEE=2"

# Get the SIM card number
# Result: Long number string, possible letters also
AT_SIM_NUMBER = "AT+CCID"

# Check if connected to network.
# Result: "+COPS: 0,0,[network]"
AT_NETWORK_STATUS = "AT+COPS?"

# Signal strength. Number should be greater than 5
# Result: "+CSQ: [number],0"
AT_SIGNAL_STRENGTH = "AT+CSQ"

# Battery state.
# Result: "+CBC: 0,[battery],[voltage]
# battery = battery percentage, voltage = actual voltage in mV
AT_BATTERY = "AT+CBC"

# Set Text mode
AT_TEXT_MODE = "AT+CMGF=1"




#################
# Constants
#################
SERIAL_PORT = "/dev/ttyUSB0"

#################
# FONA object
#################
class Fona:
    def __init__(self, serial_port="/dev/ttyAMA0", key=None, ps=None, ns=None, reset=None, ri=None):
        # Setup the serial connection
        self.__my_port = serial.Serial()
        try:
            self.__my_port.port = serial_port
            self.__my_port.baudrate = 115200
            self.__my_port.stopbits = serial.STOPBITS_ONE
            self.__my_port.bytesize = serial.EIGHTBITS
            self.__my_port.parity = serial.PARITY_NONE
            self.__my_port.timeout = 3
        finally:
            self.__connected = False
        # GPIO setup
        # See if we have a mode already
        cur_mode = GPIO.getmode()
        # If it's not set, set it to BCM.
        if cur_mode == GPIO.UNKNOWN:
            GPIO.setmode(GPIO.BCM)
        else:
            # Go with whatever has already been set. We dont' care.
            pass

        # Setup the pin connections
        self.__key_pin = key
        self.__ps_pin = ps
        self.__ns_pin = ns
        self.__reset_pin = reset
        self.__ri_pin = ri

    def connect(self):
        try:
            self.__my_port.open()
            self.__connected = True
        finally:
            pass

    @property
    def key_pin(self):
        return self.__key_pin

    @key_pin.setter
    def key_pin(self, pin):
        assert type(pin) == int, "Key pin value not an integer"
        assert pin > 0, "Invalid pin number"
        # If there was a previous pin, clean it up.
        if self.__key_pin:
            GPIO.cleanup(self.__key_pin)
        self.__key_pin = pin
        # Setup the pin in low mode. Could use an NPN transistor to trigger key to low for a power
        # switch
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    # Just toggle the key pin state. Timing and such is left to the user.
    def key_toggle(self):
        GPIO.output(self.__key_pin, not GPIO.input(self.__key_pin))

    @property
    def ps_pin(self):
        return self.__ps_pin

    @ps_pin.setter
    def ps_pin(self, pin):
        assert type(pin) == int, "Key pin value not an integer"
        assert pin > 0, "Invalid pin number"
        # If it's already set, cleanup the previous pin.
        if self.__ps_pin:
            GPIO.cleanup(self.__ps_pin)
        self.__ps_pin = pin
        # Set the pin to input mode. Should use a resistor to force up or down.
        GPIO.setup(pin, GPIO.IN)

    @property
    def ns_pin(self):
        return self.__ns_pin

    @ns_pin.setter
    def ns_pin(self, pin):
        assert type(pin) == int, "Key pin value not an integer"
        assert pin > 0, "Invalid pin number"
        if self.__ns_pin:
            GPIO.cleanup(self.__ns_pin)
        self.__ns_pin = pin
        # Set this to input, low by default.
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        # We should set up actual edge detection here. I'll do that later.
        # TODO: Add edge detection so we know the current network status.

    @property
    def reset_pin(self):
        return self.__reset_pin

    @reset_pin.setter
    def reset_pin(self, pin):
        assert type(pin) == int, "Key pin value not an integer"
        assert pin > 0, "Invalid pin number"
        if self.__reset_pin:
            GPIO.cleanup(self.__reset_pin)
        self.__reset_pin = pin
        # Like the Key pin, to actually use this you need more hardware.
        # Setting to output and low.
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

    @property
    def ri_pin(self):
        return self.__ri_pin

    @ri_pin.setter
    def ri_pin(self, pin):
        assert type(pin) == int, "Key pin value not an integer"
        assert pin > 0, "Invalid pin number"
        if self.__ri_pin:
            GPIO.cleanup(self.__ri_pin)
        self.__ri_pin = pin
        # The pin should be high by default. If it goes low for 120 ms, it's a signal
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # TODO: Add edge detection here so we can do a notification of some kind.

    @property
    def connected(self):
        return self.__connected

    def get_module_name(self):
        if self.__connected:
            self.__my_port.write(COMMAND_ATI + "\n")
            response = self.__my_port.readline()
            return response
        else:
            raise serial.SerialException("Serial connection not established.")

    def get_network_status(self):
        if self.__connected:
            self.__my_port.write(AT_NETWORK_STATUS + "\n")
            response = self.__my_port.readline()
            return response


#################
# Test FONA
#################
