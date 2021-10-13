import time

from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LED


def main():
    """
    This example switches the LEDs within the LED bar in a flowing manner. It runs with the circuit described on page 72
    of the tutorial.
    """

    setup()

    delay_seconds = 0.03

    leds = [
        LED(output_pin=pin, reverse=True)
        for pin in [11, 12, 13, 15, 16, 18, 22, 3, 5, 24]
    ]

    for led in leds:
        led.set(LED.State(on=False))

    leds[0].set(LED.State(on=True))

    try:

        while True:
            for i in range(1, len(leds)):
                time.sleep(delay_seconds)
                leds[i-1].set(LED.State(on=False))
                leds[i].set(LED.State(on=True))

            for i in reversed(range(len(leds) - 1)):
                time.sleep(delay_seconds)
                leds[i+1].set(LED.State(on=False))
                leds[i].set(LED.State(on=True))

    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
