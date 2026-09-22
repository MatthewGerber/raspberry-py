import time
from datetime import timedelta
from typing import Optional

import RPi.GPIO as gpio
import microcontroller

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.examples.led_strip import run
from raspberry_py.gpio.lights import Pi5PixelBuffer, LedStrip


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
    run(led_strip)
    led_strip.set_brightness(1.0)
    led_strip.strobe(
        LedStrip.WHITE,
        timedelta(milliseconds=20),
        timedelta(milliseconds=20),
        timedelta(seconds=10)
    )

    curr_i: Optional[int] = None
    for mm in range(100):
        print(f'mm:  {mm}')
        new_i = led_strip.set_led_at_distance(mm, LedStrip.WHITE)
        if new_i != curr_i:
            if curr_i is not None:
                led_strip[curr_i] = LedStrip.OFF
            led_strip[new_i] = LedStrip.WHITE
            curr_i = new_i
            led_strip.show()
        time.sleep(0.1)

    led_strip.step_through(LedStrip.WHITE, timedelta(milliseconds=10), 20)
    led_strip.animal_chase(timedelta(milliseconds=100))

    cleanup()


if __name__ == '__main__':
    main()
