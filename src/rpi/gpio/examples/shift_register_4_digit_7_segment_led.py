import time
from datetime import timedelta

from rpi.gpio import setup, CkPin, cleanup
from rpi.gpio.ic_chips import ShiftRegister
from rpi.gpio.lights import SevenSegmentLedShiftRegister, FourDigitSevenSegmentLED


def main():
    """
    This example drives a 4-digit, 7-segment LED with an 8-bit shift register. It runs with the circuit shown on page
    220 of the tutorial.
    """

    setup()

    # create 8-bit shift register
    shift_register = ShiftRegister(
        bits=8,
        output_disable_pin=CkPin.GPIO12,  # optional -- could hard-wire ic pin to ground instead for always enabled
        serial_data_input_pin=CkPin.GPIO24,
        shift_register_pin=CkPin.GPIO18,
        write_register_to_output_pin=CkPin.GPIO23,
        register_active_pin=CkPin.GPIO16  # optional -- could hard-wire ic pin to 3.3v for always active
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

    four_digit_led = FourDigitSevenSegmentLED(
        led_0_transistor_base_pin=CkPin.GPIO17,
        led_1_transistor_base_pin=CkPin.GPIO27,
        led_2_transistor_base_pin=CkPin.GPIO22,
        led_3_transistor_base_pin=CkPin.MOSI,
        led_shift_register=led,
        led_display_time=timedelta(seconds=0.006)
    )

    # display all characters and alternate decimal point
    for i, character in enumerate(led.CHARACTER_SEGMENTS):
        four_digit_led.display(*([character, i % 2 == 0] * 4))
        time.sleep(0.75)

    four_digit_led.stop_display()

    cleanup()


if __name__ == '__main__':
    main()
