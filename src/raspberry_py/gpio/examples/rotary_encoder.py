import time
from RPi import GPIO as gpio
from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import RotaryEncoder


def main():
    """
    Example.
    """

    setup()

    encoder = RotaryEncoder(
        phase_a_pin=CkPin.GPIO21,
        phase_b_pin=CkPin.GPIO20,
        phase_changes_per_rotation=2400
    )

    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
