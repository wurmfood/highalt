#####################################################################
#
# Module to support the Adafruit FONA vi Python for the Raspberry Pi.
#
# This assumes there is a USB->Serial cable being used. If going directly to the FONA using the
# Pi's serial pins, adjust in pin connections accordingly.
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

# Send text message



#################
# Constants
#################
SERIAL_PORT = "/dev/ttyUSB0"

#################
# Test FONA
#################
