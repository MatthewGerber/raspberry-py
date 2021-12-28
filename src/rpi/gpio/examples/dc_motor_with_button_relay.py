import time

import RPi.GPIO as gpio

from rpi.gpio import CkPin, setup, cleanup
from rpi.gpio.controls import TwoPoleButton


def main():
    """
    This example drives a DC motor as shown on page 176 of the tutorial.
    """

    setup()

    transistor_base_pin = CkPin.GPIO17
    gpio.setup(transistor_base_pin, gpio.OUT)
    button = TwoPoleButton(CkPin.GPIO18, 300)
    button.event(lambda s: gpio.output(transistor_base_pin, gpio.HIGH if s.pressed else gpio.LOW))

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
