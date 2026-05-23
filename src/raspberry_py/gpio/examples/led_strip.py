from datetime import timedelta

from rpi_ws281x import Color

from raspberry_py.gpio import CkPin
from raspberry_py.gpio.lights import LedStrip


def main():

    led_strip = LedStrip(
        led_count=144,
        led_pin=CkPin.MOSI
    )

    while True:
        try:
            led_strip.theater_chase(Color(0, 255, 0), iterations=10, wait=timedelta(milliseconds=50))
        except KeyboardInterrupt:
            led_strip.turn_off()
            break
        except:
            pass


if __name__ == '__main__':
    main()
