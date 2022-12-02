import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.sensors import UltrasonicRangeFinder


def main():
    """
    This example measures distance with an ultrasonic range finder. It runs with the circuit described on page 280 of
    the tutorial.
    """

    setup()

    sensor = UltrasonicRangeFinder(
        trigger_pin=CkPin.GPIO23,
        echo_pin=CkPin.GPIO24,
        measurements_per_second=2
    )

    sensor.event(lambda s: print(str(s)))
    sensor.start_measuring_distance()
    try:
        time.sleep(300)
    except KeyboardInterrupt:
        pass

    sensor.stop_measuring_distance()
    cleanup()


if __name__ == '__main__':
    main()
