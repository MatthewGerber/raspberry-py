import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.sensors import Tachometer


def main():
    """
    This example demonstrates a tachometer reading from a GPIO input pin that switches between low and high.
    """

    setup()

    # create a tachometer
    tachometer = Tachometer(CkPin.GPIO23)
    tachometer.event(lambda s: print(f'{s.rotations_per_second}'))
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
