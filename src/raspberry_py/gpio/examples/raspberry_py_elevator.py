from datetime import timedelta

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.robotics import RaspberryPyElevator


def main():
    """
    This example moves an elevator up and down. See
    https://matthewgerber.github.io/raspberry-py/raspberry-py/elevator.html for details.
    """

    setup()

    elevator = RaspberryPyElevator(
        left_stepper_pins=(CkPin.CE1, CkPin.CE0, CkPin.GPIO25, CkPin.GPIO24),
        right_stepper_pins=(CkPin.GPIO21, CkPin.GPIO20, CkPin.GPIO16, CkPin.GPIO12),
        location_mm=0.0,
        steps_per_mm=500.0 / 13.0,
        reverse_right_stepper=True
    )
    elevator.start()

    elevator.move(10, timedelta(seconds=2))
    elevator.move(-10, timedelta(seconds=2))
    elevator.stop()

    cleanup()


if __name__ == '__main__':
    main()
