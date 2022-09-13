import time

import RPi.GPIO as gpio
from smbus2 import SMBus

from rpi.gpio import setup, cleanup, CkPin
from rpi.gpio.adc import ADS7830
from rpi.gpio.lights import LED
from rpi.gpio.sensors import Photoresistor


def main():
    """
    This example illuminates an LED based on the value of a photoresistor via analog-to-digital conversion. It runs with
    the circuit described on page 143 of the tutorial.
    """

    setup()

    # create a pwm-driven LED
    led = LED(output_pin=CkPin.GPIO17)
    led_pwm = gpio.PWM(led.output_pin, 500)
    led_pwm.start(0)

    photoresistor_channel = 0

    # create a/d converter
    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={photoresistor_channel: (0, 100)}
    )

    # create thermistor on adc
    photoresistor = Photoresistor(
        adc=adc,
        channel=photoresistor_channel
    )

    try:
        while True:
            light_level = photoresistor.get_light_level()
            led_pwm.ChangeDutyCycle(100.0 - light_level)
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass

    led_pwm.stop()
    adc.close()
    cleanup()


if __name__ == '__main__':
    main()
