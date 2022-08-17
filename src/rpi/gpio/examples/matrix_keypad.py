import time

from rpi.gpio import setup, cleanup, CkPin
from rpi.gpio.controls import MatrixKeypad


def main():

    setup()

    keypad = MatrixKeypad(
        key_matrix=[
            ['', '', '', ''],
            ['', '', '', ''],
            ['', '', '', ''],
            ['', '', '', '']
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
        bounce_time_ms=200
    )

    keypad.event(lambda s: print(f'New state:  {s}'))
    keypad.start()
    time.sleep(30)
    keypad.stop()

    cleanup()


if __name__ == '__main__':
    main()
