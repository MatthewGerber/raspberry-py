import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import TwoPoleButton
from raspberry_py.gpio.lights import LED


def main():
    """
    This example switches an LED on and off using a button. It runs with the circuit described on page 59 of the
    tutorial.
    """

    setup()

    # create an led
    led = LED(output_pin=CkPin.GPIO17)

    # create a button
    button = TwoPoleButton(input_pin=CkPin.GPIO18, bounce_time_ms=50, read_delay_ms=50)

    # turn the led on when the button is pressed
    button.event(lambda s: led.turn_on() if s.pressed else led.turn_off())

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
