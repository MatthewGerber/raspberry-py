import RPi.GPIO as gpio
import board
import neopixel

from raspberry_py.gpio import setup
from raspberry_py.gpio.examples.led_strip import run
from raspberry_py.gpio.lights import LedStrip

setup(gpio.BCM)
pixels = neopixel.NeoPixel(board.MOSI, 144, brightness=0.1, auto_write=False)
led_strip = LedStrip(pixels)
run(led_strip)
