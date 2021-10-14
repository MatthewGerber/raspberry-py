import time

import RPi.GPIO as gpio

from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LED


def main():
    """
    This example gradually switches an LED from off to full brightness and then back to off. It runs with the circuit
    described on page 80 of the tutorial.
    """

    setup()

    # create an led on output pin 11
    led = LED(output_pin=12)

    # configure pulse-width modulation
    pwm = gpio.PWM(led.output_pin, 500)
    pwm.start(0)

    try:
        while True:

            # increase brightness
            for duty_cycle in range(0, 101):
                pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.01)

            # decrease brightness
            for duty_cycle in range(100, -1, -1):
                pwm.ChangeDutyCycle(duty_cycle)
                time.sleep(0.01)

    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
