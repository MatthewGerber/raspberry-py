import time

from rpi.gpio import CkPin, setup, cleanup
from rpi.gpio.ic_chips import ShiftRegister


def main():

    setup()

    shift_register = ShiftRegister(
        bits=8,
        output_disable_pin=CkPin.GPIO4,
        serial_data_input_pin=CkPin.GPIO17,
        shift_register_pin=CkPin.GPIO22,
        write_register_to_output_pin=CkPin.GPIO27,
        register_reset_pin=CkPin.GPIO5
    )

    shift_register.enable()

    # shift_register.write(5)

    # shift_register.clear()

    # flow leds back and forth
    for i in range(0, 8):
        shift_register.write(1 << i)
        time.sleep(0.25)

    for i in range(6, -2, -1):
        shift_register.write(1 << i if i >= 0 else i >> abs(i))
        time.sleep(0.25)

    # display binary values across full range
    for i in range(0, 2**8):
        shift_register.write(i)
        print(str(i))
        time.sleep(0.25)

    # shift_register.clear()

    cleanup()


if __name__ == '__main__':
    main()
