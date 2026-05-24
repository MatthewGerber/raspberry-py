import RPi.GPIO as gpio
import microcontroller
import neopixel

from raspberry_py.gpio import setup, CkPin
from raspberry_py.gpio.examples.led_strip import run
from raspberry_py.gpio.lights import LedStrip


def main():
    """
    Run an LED strip test for Raspberry Pi 4. Tested with the following LED strip:

        https://www.amazon.com/dp/B0BDS7NHQM?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1

    """

    setup(gpio.BCM)
    pixels = neopixel.NeoPixel(microcontroller.Pin(CkPin.MOSI.value), 144, brightness=0.1, auto_write=False)
    led_strip = LedStrip(pixels)
    run(led_strip)


if __name__ == '__main__':
    main()
