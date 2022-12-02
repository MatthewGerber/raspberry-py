import time
from datetime import timedelta

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.integrated_circuits import ShiftRegister74HC595
from raspberry_py.gpio.lights import LedMatrix


def main():
    """
    This example drives an LED matrix with two 8-bit shift registers connected in series. It runs with the circuit shown
    on page 234 of the tutorial.
    """

    setup()

    # create 8-bit shift register
    shift_register = ShiftRegister74HC595(
        bits=8,
        output_disable_pin=None,
        serial_data_input_pin=CkPin.GPIO17,
        shift_register_pin=CkPin.GPIO22,
        write_register_to_output_pin=CkPin.GPIO27,
        register_active_pin=None
    )
    shift_register.clear()

    # create led matrix and display a smile for 5 seconds
    led_matrix = LedMatrix(
        rows=8,
        cols=8,
        shift_register=shift_register,
        frame_scan_delay=timedelta(seconds=0.003)
    )
    led_matrix.display(LedMatrix.SMILE_8x8)
    time.sleep(10)

    # cleanup
    led_matrix.stop_display_thread()
    shift_register.clear()
    cleanup()


if __name__ == '__main__':
    main()
