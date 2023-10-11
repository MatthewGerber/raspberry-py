import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import TwoPoleButton
from raspberry_py.gpio.lights import LedBar


def main():
    """
    This example switches the LEDs within the LED bar in a flowing manner, and it does this once each time a button is
    pressed. It runs with the circuit described on page 72 of the tutorial, with the addition of a button circuit like
    the one shown on page 59.
    """

    setup()

    led_bar = LedBar(
        output_pins=[
            CkPin.GPIO17,
            CkPin.GPIO18,
            CkPin.GPIO27,
            CkPin.GPIO22,
            CkPin.GPIO23,
            CkPin.GPIO24,
            CkPin.GPIO25,
            CkPin.SDA1,
            CkPin.SCL1,
            CkPin.CE0
        ],
        reverse=True
    )

    button = TwoPoleButton(input_pin=CkPin.GPIO12, bounce_time_ms=50, read_delay_ms=50)

    button.event(lambda s: led_bar.flow(0.03) if s.pressed else None)

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
