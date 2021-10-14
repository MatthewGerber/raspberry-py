from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LedBar


def main():
    """
    This example switches the LEDs within the LED bar in a flowing manner. It runs with the circuit described on page 72
    of the tutorial.
    """

    setup()

    led_bar = LedBar(
        output_pins=[11, 12, 13, 15, 16, 18, 22, 3, 5, 24],
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
