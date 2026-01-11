import time

import serial
from serial import Serial

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.communication import LockingSerial
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example of using an Arduino interface to a rotary encoder.
    """

    setup()
    locking_serial = LockingSerial(
        connection=Serial(
            port='/dev/serial0',
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        ),
        throughput_step_size=1.0,
        manual_buffer=False
    )
    arduino_interface = RotaryEncoder.Arduino(
        phase_a_pin=3,
        phase_b_pin=5,
        phase_changes_per_rotation=1200,
        phase_change_mode=RotaryEncoder.PhaseChangeMode.ONE_SIGNAL_TWO_EDGE,
        angular_velocity_step_size=1.0,
        angular_acceleration_step_size=1.0,
        serial=locking_serial,
        identifier=1,
        state_update_hz=20
    )
    encoder = RotaryEncoder(arduino_interface)
    encoder.start()
    try:
        while True:
            time.sleep(1.0 / arduino_interface.state_update_hz)
            encoder.update_state()
            state: RotaryEncoder.State = encoder.get_state()
            print(
                f'Net total degrees:  {state.net_total_degrees}\n'
                f'Degrees:  {state.degrees}\n'
                f'Clockwise:  {state.clockwise}\n'                
                f'Velocity:  {state.angular_velocity} deg/s\n'
                f'Acceleration:  {state.angular_acceleration} deg/s^2\n'
            )
    except KeyboardInterrupt:
        pass
    encoder.cleanup()
    locking_serial.connection.close()
    cleanup()


if __name__ == '__main__':
    main()
