import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example of using a rotary encoder in each of several phase-change modes.
    """

    setup()

    try:
        for phase_change_mode in RotaryEncoder.PhaseChangeMode:
            print(f'Running in phase-change mode:  {phase_change_mode}...')
            encoder = RotaryEncoder(
                phase_a_pin=CkPin.GPIO17,
                phase_b_pin=(
                    CkPin.GPIO27 if phase_change_mode == RotaryEncoder.PhaseChangeMode.TWO_SIGNAL_TWO_EDGE
                    else None
                ),
                phase_change_mode=phase_change_mode
            )
            for _ in range(10):
                phase_changes_start = encoder.num_phase_changes
                time.sleep(1.0)
                phase_changes_end = encoder.num_phase_changes
                print(
                    f'Phase-change index:  {encoder.phase_change_index.value}\n'
                    f'Clockwise:  {bool(encoder.clockwise.value)}\n'
                    f'Phase changes per second:  {(phase_changes_end - phase_changes_start)}\n'
                )
            encoder.cleanup()
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
