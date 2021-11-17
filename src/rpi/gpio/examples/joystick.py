import time

from smbus2 import SMBus

from rpi.gpio import setup, cleanup, CkPin
from rpi.gpio.adc import ADS7830
from rpi.gpio.controls import Joystick


def main():
    """
    This example displays the value of an analog component (e.g., potentiometer) via an analog-to-digital converter, as
    shown on page 115 of the tutorial.
    """

    setup()

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

    joystick = Joystick(
        adc=adc,
        x_channel=joystick_x_ad_channel,
        y_channel=joystick_y_ad_channel,
        z_pin=CkPin.GPIO18,
        invert_y=True
    )

    try:
        while True:
            adc.update_state()
            print(f'{joystick.state}')
            time.sleep(0.5)
    except KeyboardInterrupt:
        adc.close()
        cleanup()


if __name__ == '__main__':
    main()
