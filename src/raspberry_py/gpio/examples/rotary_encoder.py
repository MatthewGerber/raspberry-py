import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example.
    """

    setup()

    encoder = RotaryEncoder(
        phase_a_pin=CkPin.GPIO17,
        phase_b_pin=CkPin.GPIO27,
        phase_changes_per_rotation=2400,
        report_state=None,
        degrees_per_second_step_size=0.25,
        bounce_time_ms=None,
        state_updates_per_second=10.0
    )

    try:
        while True:
            phase_changes_start = encoder.num_phase_changes
            time.sleep(1.0)
            phase_changes_end = encoder.num_phase_changes
            encoder.update_state()
            print(
                f'Degrees:  {encoder.degrees:.1f}\n'
                f'Degrees / second:  {encoder.degrees_per_second:.1f}\n'
                f'Clockwise:  {encoder.clockwise}\n'
                f'Phase changes per second:  {(phase_changes_end - phase_changes_start)}\n'
                f'RPM:  {(encoder.degrees_per_second.get_value() / 360.0) * 60.0:.1f}\n'
            )
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
