import time
from datetime import timedelta

from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.sequence import AnimationSequence
from rpi_ws281x import Color

from raspberry_py.gpio.lights import LedStrip


def run(
        led_strip: LedStrip
):
    """
    Run an LED strip.

    :param led_strip: LED strip.
    """

    # run a solid color for a couple seconds
    led_strip.pixels[0] = Color(255, 0, 0)
    led_strip.pixels.show()
    time.sleep(2)

    # run animations using the adafruit library
    pixels = led_strip.pixels
    rainbow = Rainbow(pixels, speed=0.02, period=2)
    rainbow_chase = RainbowChase(pixels, speed=0.02, size=5, spacing=3)
    rainbow_comet = RainbowComet(pixels, speed=0.02, tail_length=7, bounce=True)
    rainbow_sparkle = RainbowSparkle(pixels, speed=0.02, num_sparkles=15)
    animations = AnimationSequence(
        rainbow,
        rainbow_chase,
        rainbow_comet,
        rainbow_sparkle,
        advance_interval=5,
        auto_clear=True,
    )
    try:
        while True:
            animations.animate()
    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(.02)
        pixels.fill(0)
        pixels.show()

    # run some raspberry pi-layer stuff
    try:
        while True:
            led_strip.theater_chase(Color(0, 255, 0), iterations=10, delay=timedelta(milliseconds=50))
    except KeyboardInterrupt:
        pass
    finally:
        led_strip.turn_off()
