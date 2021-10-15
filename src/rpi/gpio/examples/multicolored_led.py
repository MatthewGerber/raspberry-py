import random
import time

import RPi.GPIO as gpio

from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LED


def main():
    """
    This example changes the color of a multi-colored LED. It runs with the circuit described on page 92 of the
    tutorial.
    """

    setup()

    # create leds and their pulse-wave modulators
    led_r = LED(output_pin=11)
    pwm_r = gpio.PWM(led_r.output_pin, 2000)
    pwm_r.start(0)

    led_g = LED(output_pin=12)
    pwm_g = gpio.PWM(led_g.output_pin, 2000)
    pwm_g.start(0)

    led_b = LED(output_pin=13)
    pwm_b = gpio.PWM(led_b.output_pin, 2000)
    pwm_b.start(0)

    def set_pwms(
            r: float,
            g: float,
            b: float,
            duration_sec: float
    ):
        """
        Set pulse-wave modulators and hold for a duration.

        :param r: Red duty cycle [0,100].
        :param g: Green duty cycle [0,100].
        :param b: Blue duty cycle [0,100].
        :param duration_sec: Duration to hold.
        """

        pwm_r.ChangeDutyCycle(r)
        pwm_g.ChangeDutyCycle(g)
        pwm_b.ChangeDutyCycle(b)
        time.sleep(duration_sec)

    # show pure red/green/blue
    set_pwms(0.0, 100.0, 100.0, 1.0)
    set_pwms(100.0, 0.0, 100.0, 1.0)
    set_pwms(100.0, 100.0, 0.0, 1.0)

    # random colors
    try:
        while True:
            set_pwms(
                random.randint(0, 100),
                random.randint(0, 100),
                random.randint(0, 100),
                0.1
            )
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
