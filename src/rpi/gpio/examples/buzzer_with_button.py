import time

from rpi.gpio import setup, cleanup
from rpi.gpio.sounds import ActiveBuzzer
from rpi.gpio.switches import TwoPoleButton


def main():
    """
    This example buzzes an active buzzer when a button is pressed. It runs with the circuit described on page 96 of the
    tutorial.
    """

    setup()

    buzzer = ActiveBuzzer(output_pin=11)

    button = TwoPoleButton(input_pin=12, bounce_time_ms=200)

    button.event(lambda s: buzzer.buzz() if s.pressed else buzzer.stop())

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
