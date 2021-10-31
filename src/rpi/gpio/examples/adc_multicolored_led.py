import time

from rpi.gpio import Clock
from rpi.gpio.adc import AdcDevice


def main():
    """
    This example uses three analog-to-digital converters to control the red, green, and blue components of a
    multicolored LED.
    """

    adc = AdcDevice.detect_i2c('/dev/i2c-1', (0, 100))

    clock = Clock(tick_interval_seconds=0.5)

    clock.event(lambda _: adc.update_state(0) and adc.update_state(1) and adc.update_state(2))

    adc.event(lambda s: print(str(s)))

    clock.start()
    time.sleep(20)
    clock.stop()

    adc.close()


if __name__ == '__main__':
    main()
