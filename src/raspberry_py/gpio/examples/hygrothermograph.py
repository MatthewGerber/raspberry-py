import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import Hygrothermograph


def main():
    """
    This example displays the values of a hygrothermograph, as shown on page 255 of the tutorial.
    """

    setup()

    sensor = Hygrothermograph(pin=CkPin.GPIO17)
    sensor.event(
        action=lambda s: print(f'New reading:  {s}'),
        trigger=lambda s: s.status == Hygrothermograph.State.Status.OK
    )
    try:
        while True:
            sensor.read(5)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
