import time

from raspberry_py.gpio import setup, CkPin, cleanup
from raspberry_py.gpio.integrated_circuits import ShiftRegister74HC595
from raspberry_py.gpio.lights import SevenSegmentLedShiftRegister


def main():
    """
    This example drives a 7-segment LED with an 8-bit shift register. It runs with the circuit shown on page 213 of the
    tutorial.
    """

    setup()

    # create 8-bit shift register
    shift_register = ShiftRegister74HC595(
        bits=8,
        output_disable_pin=CkPin.GPIO4,  # optional -- could hard-wire ic pin to ground instead for always enabled
        serial_data_input_pin=CkPin.GPIO17,
        shift_register_pin=CkPin.GPIO22,
        write_register_to_output_pin=CkPin.GPIO27,
        register_active_pin=CkPin.GPIO5  # optional -- could hard-wire ic pin to 3.3v for always active
    )
    shift_register.enable()
    shift_register.clear()

    # create led
    led = SevenSegmentLedShiftRegister(
        shift_register=shift_register,
        segment_shift_register_output={
            SevenSegmentLedShiftRegister.Segment.A: 0,
            SevenSegmentLedShiftRegister.Segment.B: 1,
            SevenSegmentLedShiftRegister.Segment.C: 2,
            SevenSegmentLedShiftRegister.Segment.D: 3,
            SevenSegmentLedShiftRegister.Segment.E: 4,
            SevenSegmentLedShiftRegister.Segment.F: 5,
            SevenSegmentLedShiftRegister.Segment.G: 6,
            SevenSegmentLedShiftRegister.Segment.DECIMAL_POINT: 7
        }
    )

    # display all characters and alternate decimal point
    for i, character in enumerate(led.CHARACTER_SEGMENTS):
        led.display(character, i % 2 == 0)
        time.sleep(0.5)

    cleanup()


if __name__ == '__main__':
    main()
