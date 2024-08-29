import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import MultiprocessRotaryEncoder, RotaryEncoder


def main():
    """
    Example of using a multiprocess rotary encoder in each of several phase-change modes.
    """

    setup()

    try:
        for phase_change_mode in RotaryEncoder.PhaseChangeMode:
            print(f'Running in phase-change mode:  {phase_change_mode}...')
            encoder = MultiprocessRotaryEncoder(
                phase_a_pin=CkPin.GPIO17,
                phase_b_pin=CkPin.GPIO27,
                phase_changes_per_rotation=1200,
                phase_change_mode=phase_change_mode,
                angular_velocity_step_size=0.5,
                angular_acceleration_step_size=0.5
            )
            encoder.wait_for_startup()
            start_epoch = time.time()
            while time.time() - start_epoch < 10.0:
                time.sleep(1.0/20.0)
                encoder.update_state(True)
                state: MultiprocessRotaryEncoder.State = encoder.state
                print(
                    f'Degrees:  {state.degrees}; RPM:  {60.0 * state.angular_velocity / 360.0:.1f} '
                    f'(clockwise={state.clockwise})'
                )
            encoder.wait_for_termination()
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
