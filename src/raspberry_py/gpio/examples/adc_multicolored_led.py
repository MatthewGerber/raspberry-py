import time

from smbus2 import SMBus

from raspberry_py.gpio import Clock, setup, CkPin, cleanup
from raspberry_py.gpio.adc import ADS7830
from raspberry_py.gpio.lights import MulticoloredLED


def main():
    """
    This example uses three analog potentiometers with an ADC to control the red, green, and blue components of a
    multicolored LED. It runs on the circuit shown on page 134 of the tutorial.
    """

    setup()

    # create multicolored led
    led = MulticoloredLED(
        r_pin=CkPin.GPIO16,
        g_pin=CkPin.GPIO20,
        b_pin=CkPin.GPIO21,
        common_anode=True
    )

    # create adc and rescale its three digital outputs to be in [0, 100]
    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={0: (0, 100), 1: (0, 100), 2: (0, 100)}
    )

    # set up a clock and update the adc each tick
    clock = Clock(tick_interval_seconds=0.5)
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
