import time
from datetime import timedelta, datetime

import serial
from serial import Serial

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.communication import LockingSerial
from raspberry_py.gpio.motors import Stepper, StepperMotorDriverArduinoUln2003


def main():
    """
    This example rotates a stepper motor via Arduino driver.
    """

    setup()

    locking_serial = LockingSerial(
        connection=Serial(
            port='/dev/serial0',
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        ),
        throughput_step_size=0.05
    )

    # create/start stepper
    stepper = Stepper(
        poles=32,
        output_rotor_ratio=1/64.0,
        driver=StepperMotorDriverArduinoUln2003(
            driver_pin_1=5,
            driver_pin_2=6,
            driver_pin_3=7,
            driver_pin_4=8,
            identifier=0,
            serial=locking_serial
        ),
        reverse=False
    )

    stepper.start()

    # rotate 45 degrees in 1 second
    start = datetime.now()
    stepper.step_degrees(45, timedelta(seconds=1))
    print(f'Rotated to {stepper.get_degrees():.1f} degrees in {(datetime.now() - start).total_seconds():.1f} seconds.')

    time.sleep(1)

    # rotate -190 degrees in 5 seconds
    start = datetime.now()
    stepper.step_degrees(-190, timedelta(seconds=5))
    print(f'Rotated to {stepper.get_degrees():.1f} degrees in {(datetime.now() - start).total_seconds():.1f} seconds.')

    # clean up
    stepper.stop()
    cleanup()


if __name__ == '__main__':
    main()
