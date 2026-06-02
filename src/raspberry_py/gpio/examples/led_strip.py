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

    # run a solid color to check ordering
    led_strip[0] = Color(255, 0, 0)
    led_strip.show()
    print(f'Red...{led_strip[0]}')
    time.sleep(1)
    led_strip[0] = Color(0, 255, 0)
    led_strip.show()
    print(f'Green...{led_strip[0]}')
    led_strip.show()
    time.sleep(1)
    led_strip.pixels[0] = Color(0, 0, 255)
    led_strip.show()
    print(f'Blue...{led_strip[0]}')
    time.sleep(1)

    # run animations using the adafruit library
    print(f'Adafruit animations...')
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
        advance_interval=1,
        auto_clear=True
    )
    try:
        start_time = time.time()
        while time.time() - start_time < 5.0:
            animations.animate()
    finally:
        led_strip.turn_off()

    try:
        # run some raspberry pi-layer stuff
        print('Color wipe...')
        led_strip.color_wipe(Color(255, 0, 0), timedelta(milliseconds=10))
        print('Rainbow...')
        led_strip.rainbow(timedelta(milliseconds=5), 1)
        print('Rainbow cycle...')
        led_strip.rainbow_cycle(timedelta(milliseconds=5), 1)
        print('Theater chase...')
        led_strip.theater_chase(Color(0, 255, 0), iterations=10, delay=timedelta(milliseconds=10))
        print('Theater chase rainbow...')
        led_strip.theater_chase_rainbow(timedelta(milliseconds=20), 1)
    finally:
        led_strip.turn_off()
