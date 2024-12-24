import time

import serial
from serial import Serial

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example of using an Arduino interface to a rotary encoder.
    """

    setup()
    ser = Serial(
        port='/dev/serial0',
        baudrate=9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    encoder = RotaryEncoder(
        RotaryEncoder.Arduino(
            phase_change_mode=RotaryEncoder.PhaseChangeMode.ONE_SIGNAL_TWO_EDGE,
            serial=ser,
            identifier=1
        ),
        phase_changes_per_rotation=1200,
        angular_velocity_step_size=1.0,
        angular_acceleration_step_size=1.0
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
                f'Velocity:  {state.angular_velocity} deg/s\n'
                f'Acceleration:  {state.angular_acceleration} deg/s^2\n'
            )
    except KeyboardInterrupt:
        pass
    encoder.cleanup()
    ser.close()
    cleanup()


if __name__ == '__main__':
    main()
