import time

import RPi.GPIO as gpio

from rpi.gpio import setup, cleanup, CkPin, Clock
from rpi.gpio.adc import AdcDevice
from rpi.gpio.lights import LED


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

    # read value from photoresistor
    adc = AdcDevice.detect_i2c('/dev/i2c-1', {0: (0, 100)})
    adc.event(lambda s: led_pwm.ChangeDutyCycle(100.0 - s.channel_value[0]))
    clock = Clock(tick_interval_seconds=0.5)
    clock.event(lambda _: adc.update_state())
    clock.start()

    time.sleep(60)
    clock.stop()
    led_pwm.stop()
    adc.close()
    cleanup()


if __name__ == '__main__':
    main()
