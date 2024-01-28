import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.sensors import Tachometer


def main():
    """
    This example demonstrates a tachometer reading from a GPIO input pin that switches between low and high.
    """

    setup()

    # create a tachometer
    tachometer = Tachometer(
        reading_pin=CkPin.GPIO23,
        bounce_time_ms=1,
        read_delay_ms=0.1,
        low_readings_per_rotation=4,
        rotations_per_second_step_size=0.02
    )
    tachometer.event(lambda s: print(f'{s.rotations_per_second:.1f} RPS'))
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
