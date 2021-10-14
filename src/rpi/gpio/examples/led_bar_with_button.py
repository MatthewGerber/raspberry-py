import time

from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LedBar
from rpi.gpio.switches import TwoPoleButton


def main():
    """
    This example switches the LEDs within the LED bar in a flowing manner, and it does this once each time a button is
    pressed. It runs with the circuit described on page 72 of the tutorial, with the addition of a button circuit like
    the one shown on page 59.
    """

    setup()

    led_bar = LedBar(
        output_pins=[11, 12, 13, 15, 16, 18, 22, 3, 5, 24],
        reverse=True,
        delay_seconds=0.03
    )

    button = TwoPoleButton(input_pin=32, bounce_time_ms=50)

    button.event(lambda _: led_bar.flow() if button.get_state().pressed else None)

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
