import RPi.GPIO as gpio
import board

from raspberry_py.gpio import setup
from raspberry_py.gpio.examples.led_strip import run
from raspberry_py.gpio.lights import Pi5PixelBuffer, LedStrip


def main():
    """
    Run an LED strip test for Raspberry Pi 5.
    """

    setup(gpio.BCM)
    pixels = Pi5PixelBuffer(board.MOSI, 144, auto_write=True, byteorder="BGR")
    led_strip = LedStrip(pixels)
    run(led_strip)


if __name__ == '__main__':
    main()
