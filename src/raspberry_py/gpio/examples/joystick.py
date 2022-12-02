import logging
import time

from smbus2 import SMBus

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.adc import ADS7830
from raspberry_py.gpio.controls import Joystick


def main():
    """
    This example displays the values of a three-axis joystick via an analog-to-digital converter, as shown on page 153
    of the tutorial.
    """

    logging.getLogger().setLevel(logging.CRITICAL)

    setup()

    # create an a/d converter for the joystick and rescale the digital outputs to be in [-1, 1].
    joystick_y_ad_channel = 0
    joystick_x_ad_channel = 1
    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={
            joystick_y_ad_channel: (-1.0, 1.0),
            joystick_x_ad_channel: (-1.0, 1.0)
        }
    )

    # create a joystick. invert the y-axis values so that pushing forward increases them.
    joystick = Joystick(
        adc=adc,
        x_channel=joystick_x_ad_channel,
        y_channel=joystick_y_ad_channel,
        z_pin=CkPin.GPIO18,
        invert_y=True
    )

    joystick.event(lambda s: print(f'{s}'))

    try:
        while True:
            joystick.update_state()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    adc.close()
    cleanup()


if __name__ == '__main__':
    main()
