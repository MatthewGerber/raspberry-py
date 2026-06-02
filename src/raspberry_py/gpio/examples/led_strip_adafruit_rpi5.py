import time
from datetime import timedelta
from typing import Optional

import RPi.GPIO as gpio
import microcontroller
import numpy as np
from rpi_ws281x import Color

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.examples.led_strip import run
from raspberry_py.gpio.lights import Pi5PixelBuffer, LedStrip, FrameLedStrip


def main():
    """
    Run an LED strip test for Raspberry Pi 5. Tested with the following LED strip:

        https://www.amazon.com/dp/B0BDS7NHQM

    """

    setup(gpio.BCM)
    pixels = Pi5PixelBuffer(
        microcontroller.Pin(int(CkPin.GPIO23)),
        144,
        byteorder='GRB',
        auto_write=False,
        brightness=0.1
    )
    led_strip = LedStrip(pixels, 7.0)
    # run(led_strip)
    # led_strip.set_brightness(1.0)
    # led_strip.strobe(
    #     LedStrip.WHITE,
    #     timedelta(milliseconds=20),
    #     timedelta(milliseconds=20),
    #     timedelta(seconds=10)
    # )
    #
    # curr_i: Optional[int] = None
    # for mm in range(100):
    #     print(f'mm:  {mm}')
    #     new_i = led_strip.set_led_at_distance(mm, LedStrip.WHITE)
    #     if new_i != curr_i:
    #         if curr_i is not None:
    #             led_strip[curr_i] = LedStrip.OFF
    #         led_strip[new_i] = LedStrip.WHITE
    #         curr_i = new_i
    #         led_strip.show()
    #     time.sleep(0.1)
    #
    # led_strip.step_through(LedStrip.WHITE, timedelta(milliseconds=10), 20)
    # led_strip.animal_chase(timedelta(milliseconds=100))

    led_frame = FrameLedStrip(pixels, 7.0, 996.95 / 4.0, 996.95 / 4.0)
    for y_mm in np.linspace(0.0, led_frame.height_mm, 20):
        for x_mm in np.linspace(0.0, led_frame.width_mm, 20):
            led_frame.corners(LedStrip.GREEN)
            led_frame.cross_point(x_mm, y_mm, LedStrip.RED)
            led_frame.show()
            time.sleep(0.05)
            led_frame.turn_off()

    led_frame.turn_off()

    cleanup()


if __name__ == '__main__':
    main()
