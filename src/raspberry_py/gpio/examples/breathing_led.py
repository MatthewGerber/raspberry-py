import time

import RPi.GPIO as gpio

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.lights import LED


def main():
    """
    This example gradually switches an LED from off to full brightness and then back to off. It runs with the circuit
    described on page 80 of the tutorial.
    """

    setup()

    # create an led
    led = LED(output_pin=CkPin.GPIO18)

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

    pwm.stop()
    cleanup()


if __name__ == '__main__':
    main()
