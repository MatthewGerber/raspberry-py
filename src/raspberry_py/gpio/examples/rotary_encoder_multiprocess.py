import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import MultiprocessRotaryEncoder


def main():
    """
    Example.
    """

    setup()

    encoder = MultiprocessRotaryEncoder(
        identifier='test',
        phase_a_pin=CkPin.GPIO17,
        phase_b_pin=CkPin.GPIO27,
        degrees_per_second_step_size=0.25,
        state_updates_per_second=10.0
    )
    encoder.wait_for_startup()

    try:
        while True:
            time.sleep(1.0)
            print(f'RPM:  {60.0 * encoder.calculate_degrees_per_second() / 360.0:.1f}')
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
