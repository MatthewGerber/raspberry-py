import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.controls import TwoPoleButton
from raspberry_py.gpio.power import Relay


def main():
    """
    This example drives a DC motor as shown on page 176 of the tutorial. It uses a two-pole button to signal a relay
    that provides power to the motor.
    """

    setup()

    relay = Relay(
        transistor_base_pin=CkPin.GPIO17
    )
    button = TwoPoleButton(CkPin.GPIO18, 300, 50)
    button.event(lambda s: relay.close() if s.pressed else relay.open())

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
