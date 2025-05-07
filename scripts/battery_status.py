#!/usr/bin/env python
import struct
import smbus
import time
import RPi.GPIO as GPIO
from subprocess import check_output, call
import datetime

CW2015_ADDRESS = 0X62
CW2015_REG_MODE = 0X0A


def read_voltage(bus):
    # This function returns as float the voltage from the Raspi UPS Hat via the provided SMBus object
    read = bus.read_word_data(CW2015_ADDRESS, 0X02)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    voltage = swapped * 0.305 / 1000
    return voltage


def read_capacity(bus):
    # This function returns as a float the remaining capacity of the battery connected to the Raspi UPS Hat via the
    # provided SMBus object
    read = bus.read_word_data(CW2015_ADDRESS, 0X04)
    swapped = struct.unpack("<H", struct.pack(">H", read))[0]
    capacity = swapped / 256
    return capacity


def quick_start(bus):
    # This function wake up the CW2015 and make a quick-start fuel-gauge calculations
    bus.write_word_data(CW2015_ADDRESS, CW2015_REG_MODE, 0x30)


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(4, GPIO.IN)  # GPIO4 is used to detect whether an external power supply is inserted

bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

quick_start(bus)

output_result = ""

output_result += "  " + "\n"
output_result += "Initialize the CW2015 ......" + "\n"

GET_THROTTLED_CMD = 'vcgencmd get_throttled'
MESSAGES = {
    0: 'Under-voltage!',
    1: 'ARM frequency capped!',
    2: 'Currently throttled!',
    3: 'Soft temperature limit active',
    16: 'Under-voltage has occurred since last reboot.',
    17: 'Throttling has occurred since last reboot.',
    18: 'ARM frequency capped has occurred since last reboot.',
    19: 'Soft temperature limit has occurred'
}

f = open("/tmp/battery_status", "w")
f.write(output_result)
f.close()

def shutdown():
    # Write intent for backup script
    with open("/tmp/bot_action", "w") as f:
        f.write("shutdown")

    call("/bin/bash /home/gektor/Discord-bot/scripts/backup.sh")


while True:
    output_result = ""
    throttled_output = check_output(GET_THROTTLED_CMD, shell=True).strip().decode("utf-8")
    throttled_binary = bin(int(str(throttled_output).split('=')[1].split('\\n')[0], 0))

    output_result += "+" + str(datetime.datetime.now()) + "++++++++" + "\n"
    output_result += str(throttled_output) + "\n"

    warnings = 0
    for position, message in MESSAGES.items():
        # Check for the binary digits to be "on" for each warning message
        if len(throttled_binary) > position and throttled_binary[0 - position - 1] == '1':
            output_result += message + "\n"
            warnings += 1
    if warnings == 0:
        output_result += "Looking good!" + "\n"
    else:
        output_result += "Houston, we may have a problem!" + "\n"

    output_result += "Voltage:%5.2fV" % read_voltage(bus) + "\n"
    output_result += "Battery:%5i%%" % read_capacity(bus) + "\n"

    if read_capacity(bus) == 100:
        output_result += "Battery FULL" + "\n"
    if read_capacity(bus) < 70:
        output_result += "Battery LOW" + "\n"

    # The following is the power plug detection judgment program of V1.2 version. GPIO is low when power is plugged in
    if GPIO.input(4) == GPIO.LOW:
        output_result += "Power Adapter Plug In" + "\n"
        if read_capacity(bus) < 5:
            output_result += "-----------------------------------" + "\n"
            output_result += "read_capacity(bus) < 5!" + "\n"

            f = open("/tmp/battery_status", "w")
            f.write(output_result)
            f.close()

            shutdown()

    if GPIO.input(4) == GPIO.HIGH:
        output_result += "Power Adapter Unplug" + "\n"
        if read_capacity(bus) < 10:
            output_result += "-----------------------------------" + "\n"
            output_result += "read_capacity(bus) < 10!" + "\n"

            f = open("/tmp/battery_status", "w")
            f.write(output_result)
            f.close()

            shutdown()

    f = open("/tmp/battery_status", "w")
    f.write(output_result)
    f.close()

    time.sleep(60)
