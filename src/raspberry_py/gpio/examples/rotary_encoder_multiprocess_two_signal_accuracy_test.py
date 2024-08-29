import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import MultiprocessRotaryEncoder, RotaryEncoder


def main():
    """
    Example of using a multiprocess rotary encoder. This runs until killed, so that two-signal phase-change loss can
    be assessed.
    """

    setup()

    encoder = MultiprocessRotaryEncoder(
        phase_a_pin=CkPin.GPIO17,
        phase_b_pin=CkPin.GPIO27,
        phase_changes_per_rotation=1200,
        phase_change_mode=RotaryEncoder.PhaseChangeMode.TWO_SIGNAL_TWO_EDGE,
        angular_velocity_step_size=0.5,
        angular_acceleration_step_size=0.5
    )
    encoder.wait_for_startup()

    try:
        while True:
            time.sleep(1.0/20.0)
            encoder.update_state(True)
            state: MultiprocessRotaryEncoder.State = encoder.state
            print(
                f'Degrees:  {state.degrees:.1f}; RPM:  {60.0 * state.angular_velocity / 360.0:.1f} '
                f'(clockwise={state.clockwise})'
            )
    except KeyboardInterrupt:
        encoder.wait_for_termination()
        time.sleep(1.0)

    cleanup()


if __name__ == '__main__':
    main()
