import time

from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LED


def main():
    """
    This example switches an LED on for 1 second then off. It runs with the circuit described on page 53 of the
    tutorial.
    """

    setup()

    # create an led on output pin 11
    led = LED(output_pin=11)

    # set on for 1 second then off
    led.turn_on()
    time.sleep(1)
    led.turn_off()

    cleanup()


if __name__ == '__main__':
    main()
