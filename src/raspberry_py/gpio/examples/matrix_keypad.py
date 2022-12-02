import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import MatrixKeypad


def main():
    """
    This example accepts input from a matrix keypad. It runs with the circuit described on page 263 of the tutorial.
    """

    setup()

    keypad = MatrixKeypad(
        key_matrix=[
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D']
        ],
        row_pins=[
            CkPin.GPIO18,
            CkPin.GPIO23,
            CkPin.GPIO24,
            CkPin.GPIO25
        ],
        col_pins=[
            CkPin.MOSI,
            CkPin.GPIO22,
            CkPin.GPIO27,
            CkPin.GPIO17
        ],
        scans_per_second=10
    )

    keypad.event(lambda s: print(f'{s.keys_pressed}'))
    keypad.start_scanning()
    try:
        time.sleep(300)
    except KeyboardInterrupt:
        pass

    keypad.stop_scanning()
    cleanup()


if __name__ == '__main__':
    main()
