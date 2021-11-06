import time

from smbus2 import SMBus

from rpi.gpio.adc import ADS7830
from rpi.gpio.sensors import Thermistor


def main():
    """
    This example displays the value of a thermistor via an analog-to-digital converter, as shown on page 145 of the
    tutorial.
    """

    # create a/d converter
    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={0: None}
    )

    # create thermistor on adc
    thermistor = Thermistor(
        adc=adc,
        channel=0
    )

    try:
        while True:
            adc.update_state()
            print(f'Degrees (F) : {thermistor.get_temperature_f():.1f}')
            time.sleep(0.1)
    except KeyboardInterrupt:
        adc.close()


if __name__ == '__main__':
    main()
