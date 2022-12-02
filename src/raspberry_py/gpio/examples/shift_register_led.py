import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.integrated_circuits import ShiftRegister74HC595


def main():
    """
    This example drives an LED bar with an 8-bit shift register. It runs with the circuit shown on page 204 of the
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

    # flow leds back and forth once
    for i in range(0, shift_register.bits):
        shift_register.write(1 << i)
        time.sleep(0.25)

    for i in range(shift_register.bits - 2, -1, -1):
        shift_register.write(1 << i if i >= 0 else i >> abs(i))
        time.sleep(0.25)

    # display binary values across full range of register
    for i in range(0, 2**shift_register.bits):
        shift_register.write(i)
        print(str(i))
        time.sleep(0.25)

    shift_register.clear()

    cleanup()


if __name__ == '__main__':
    main()
