from datetime import timedelta

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.robotics import RaspberryPyElevator


def main():
    """
    This example demonstrates movement of the elevator up and down, presuming that the elevator has first been
    assembled. See
    https://matthewgerber.github.io/raspberry-py/raspberry-py/elevator.html for details.
    """

    setup()

    elevator = RaspberryPyElevator(
        left_stepper_pins=(CkPin.CE1, CkPin.CE0, CkPin.GPIO25, CkPin.GPIO24),
        right_stepper_pins=(CkPin.GPIO21, CkPin.GPIO20, CkPin.GPIO16, CkPin.GPIO12),
        bottom_limit_switch_input_pin=CkPin.MOSI,
        top_limit_switch_input_pin=CkPin.MISO,
        location_mm=0.0,
        steps_per_mm=38.5,
        reverse_left_stepper=False,
        reverse_right_stepper=True
    )
    elevator.start()

    elevator.move(20, timedelta(seconds=5))
    elevator.move(-20, timedelta(seconds=5))

    cleanup()


if __name__ == '__main__':
    main()
