import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example.
    """

    setup()

    encoder = RotaryEncoder(
        phase_a_pin=CkPin.GPIO21,
        phase_b_pin=CkPin.GPIO20,
        phase_changes_per_rotation=2400,
        report_state=False
    )

    for _ in range(10):
        phase_changes_start = encoder.phase_changes
        time.sleep(1.0)
        phase_changes_end = encoder.phase_changes
        print(f'Degrees:  {encoder.degrees:.1f}')
        print(f'Degrees / second:  {encoder.degrees_per_second:.1f}')
        print(f'Clockwise:  {encoder.clockwise}')
        print(f'{(phase_changes_end - phase_changes_start)} phase changes per second')

    encoder.report_state = True
    encoder.event(lambda s: print(f'{s}'))
    time.sleep(10)

    cleanup()


if __name__ == '__main__':
    main()
