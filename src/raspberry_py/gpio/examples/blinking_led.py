import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.lights import LED


def main():
    """
    This example switches an LED on for 1 second then off. It runs with the circuit described on page 40 of the
    tutorial.
    """

    setup()

    # create an led
    led = LED(output_pin=CkPin.GPIO17)

    # set on for 1 second then off
    led.turn_on()
    time.sleep(1)
    led.turn_off()

    cleanup()


if __name__ == '__main__':
    main()
