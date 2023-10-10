import time

import RPi.GPIO as gpio

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.sensors import Tachometer


def main():
    """
    This example demonstrates a tachometer reading from a GPIO input pin that switches between low and high.
    """

    setup()

    # create a tachometer
    tachometer = Tachometer(CkPin.GPIO23)

    try:
        while True:
            print(f'{gpio.input(tachometer.reading_pin)}')
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
