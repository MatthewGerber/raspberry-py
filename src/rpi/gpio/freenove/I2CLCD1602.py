#!/usr/bin/env python3
########################################################################
# Filename    : I2CLCD1602.py
# Description : Use the LCD display data
# Author      : freenove
# modification: 2018/08/03
########################################################################
from datetime import datetime
from time import sleep

from Adafruit_LCD1602 import AdafruitLCD
from PCF8574 import PCF8574_GPIO


def get_cpu_temp():
    # get CPU temperature and store it into file "/sys/class/thermal/thermal_zone0/temp"
    tmp = open('/sys/class/thermal/thermal_zone0/temp')
    cpu = tmp.read()
    tmp.close()

    return f'{float(cpu)/1000:.2f} c'


def get_time_now():     # get system time
    return datetime.now().strftime('    %H:%M:%S')


def loop():
    mcp.output(3, 1)     # turn on LCD backlight
    lcd.begin(2)     # set number of LCD lines

    while True:
        lcd.set_cursor(0, 0)  # set cursor position
        lcd.message('CPU: ' + get_cpu_temp()+'\n')
        lcd.message(get_time_now())
        sleep(1)


def destroy():
    lcd.clear()


PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        raise ValueError('I2C Address Error !')

lcd = AdafruitLCD(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], gpio=mcp)

if __name__ == '__main__':
    print('Program is starting ... ')
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
