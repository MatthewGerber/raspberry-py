#!/usr/bin/env python3
########################################################################
# Filename    : adc.py
# Description : Use ADC module to read the voltage value of potentiometer.
# Author      : www.freenove.com
# modification: 2020/03/06
########################################################################
import time

from rpi.gpio.adc.components import ADCDevice, PCF8591, ADS7830

adc = ADCDevice() # Define an ADCDevice class object

def setup():

    global adc
    if(adc.detect_i2c(0x48)): # Detect the pcf8591.
        adc = PCF8591()
    elif(adc.detect_i2c(0x4b)): # Detect the ads7830
        adc = ADS7830()
    else:
        print(f'No ADC found on either {0x48} or {0x4b}. Use command `i2cdetect -y 1` to check the I2C addresses')
        exit(-1)
        
def loop():
    while True:
        value = adc.analog_read(0)    # read the ADC value of channel 0
        voltage = value / 255.0 * 3.3  # calculate the voltage value
        print ('ADC Value : %d, Voltage : %.2f'%(value,voltage))
        time.sleep(0.1)

def destroy():
    adc.close()
    
if __name__ == '__main__':   # Program entrance
    print ('Program is starting ... ')
    try:
        setup()
        loop()
    except KeyboardInterrupt: # Press ctrl-c to end the program.
        destroy()
        
    
