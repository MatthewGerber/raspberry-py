import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example of using a direct GPIO interface to a rotary encoder.
    """

    setup()
    encoder = RotaryEncoder(
        RotaryEncoder.PiGPIO(
            phase_a_pin=CkPin.GPIO22,
            phase_b_pin=CkPin.GPIO5,
            phase_changes_per_rotation=1200,
            phase_change_mode=RotaryEncoder.PhaseChangeMode.TWO_SIGNAL_TWO_EDGE,
            angular_velocity_step_size=1.0,
            angular_acceleration_step_size=1.0
        )
    )
    encoder.start()
    try:
        while True:
            time.sleep(1.0)
            encoder.update_state(True)
            state: RotaryEncoder.State = encoder.get_state()
            print(
                f'Clockwise:  {state.clockwise}\n'
                f'Degrees:  {state.degrees}\n'
                f'Net degrees:  {state.net_total_degrees}\n'
                f'Velocity:  {state.angular_velocity} deg/s\n'
                f'Acceleration:  {state.angular_acceleration} deg/s^2\n'
            )
    except KeyboardInterrupt:
        pass
    encoder.cleanup()
    cleanup()


if __name__ == '__main__':
    main()
