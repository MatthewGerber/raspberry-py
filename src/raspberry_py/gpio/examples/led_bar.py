from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.lights import LedBar


def main():
    """
    This example switches the LEDs within the LED bar in a flowing manner. It runs with the circuit described on page 72
    of the tutorial.
    """

    setup()

    led_bar = LedBar(
        output_pins=[
            CkPin.GPIO17,
            CkPin.GPIO18,
            CkPin.GPIO27,
            CkPin.GPIO22,
            CkPin.GPIO23,
            CkPin.GPIO24,
            CkPin.GPIO25,
            CkPin.SDA1,
            CkPin.SCL1,
            CkPin.CE0
        ],
        reverse=True
    )

    try:
        while True:
            led_bar.flow(0.03)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
