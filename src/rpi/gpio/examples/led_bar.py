from rpi.gpio import setup, cleanup, CkPin
from rpi.gpio.lights import LedBar


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
            CkPin.CE0,
        ],
        reverse=True,
        delay_seconds=0.03
    )

    try:
        while True:
            led_bar.flow()
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
