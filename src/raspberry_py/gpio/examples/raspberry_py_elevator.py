from datetime import timedelta

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.robotics import RaspberryPyElevator


def main():
    """
    This example moves an elevator up and down. See
    https://matthewgerber.github.io/raspberry-py/raspberry-py/elevator.html for details.
    """

    setup()

    # TODO:  Add reverse options. Add calibration conveniences.
    elevator = RaspberryPyElevator(
        left_stepper_pins=(CkPin.CE1, CkPin.CE0, CkPin.GPIO25, CkPin.GPIO24),
        right_stepper_pins=(CkPin.GPIO12, CkPin.GPIO16, CkPin.GPIO20, CkPin.GPIO21),
        location_mm=0.0,
        steps_per_mm=1.0
    )
    elevator.start()

    elevator.move(500, timedelta(seconds=5))
    elevator.move(-500, timedelta(seconds=5))
    elevator.stop()

    cleanup()


if __name__ == '__main__':
    main()
