import RPi.GPIO as gpio
import microcontroller
import neopixel

from raspberry_py.gpio import setup, CkPin
from raspberry_py.gpio.examples.led_strip import run
from raspberry_py.gpio.lights import LedStrip


def main():
    """
    Run an LED strip test for Raspberry Pi 4. Tested with the following LED strip:

        https://www.amazon.com/dp/B0BDS7NHQM

    """

    setup(gpio.BCM)
    pixels = neopixel.NeoPixel(microcontroller.Pin(int(CkPin.MOSI)), 144, brightness=0.1, auto_write=False)
    led_strip = LedStrip(pixels, 7.0)
    run(led_strip)


if __name__ == '__main__':
    main()
