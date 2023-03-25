import time
from datetime import timedelta, datetime

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.motors import Stepper


def main():
    """
    This example rotates a stepper motor. It runs with the circuit described on page 194 of the tutorial.
    """

    setup()

    # create/start stepper
    stepper = Stepper(
        poles=32,
        output_rotor_ratio=1/64.0,
        driver_pin_1=CkPin.GPIO18,
        driver_pin_2=CkPin.GPIO23,
        driver_pin_3=CkPin.GPIO24,
        driver_pin_4=CkPin.GPIO25
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
