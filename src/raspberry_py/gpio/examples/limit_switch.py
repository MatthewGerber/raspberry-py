import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import LimitSwitch


def main():
    """
    This example demonstrates a limit switch. The circuit is similar to that of the two-pole button switch shown on page
    96 of the tutorial.
    """

    setup()

    switch = LimitSwitch(input_pin=CkPin.MOSI, bounce_time_ms=5)

    switch.event(lambda s: print(f'{s}'))

    print('You have 20 seconds to press the switch...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
