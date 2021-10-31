import time

from rpi.gpio import Clock, setup, CkPin, cleanup
from rpi.gpio.adc import AdcDevice
from rpi.gpio.lights import MulticoloredLED


def main():
    """
    This example uses three analog potentiometers with an ADC to control the red, green, and blue components of a
    multicolored LED.
    """

    setup()

    # create multicolored led
    led = MulticoloredLED(
        r_pin=CkPin.GPIO16,
        g_pin=CkPin.GPIO20,
        b_pin=CkPin.GPIO21,
        common_anode=True
    )

    # detect the adc and rescale its digital outputs to be in [0, 100]
    adc = AdcDevice.detect_i2c('/dev/i2c-1', {0: (0, 100), 1: (0, 100), 2: (0, 100)})

    # set up a clock and update the adc each tick
    clock = Clock(tick_interval_seconds=1.0)
    clock.event(lambda _: adc.update_state())

    # set the led color components to the adc outputs
    adc.event(lambda s: led.set(*s.channel_value.values()))

    # start
    clock.start()
    time.sleep(2000)

    # cleanup
    clock.stop()
    adc.close()
    cleanup()


if __name__ == '__main__':
    main()
