import time

from smbus2 import SMBus

from raspberry_py.gpio import cleanup
from raspberry_py.gpio.adc import ADS7830
from raspberry_py.gpio.sensors import Thermistor


def main():
    """
    This example displays the value of a thermistor via an analog-to-digital converter, as shown on page 145 of the
    tutorial.
    """

    thermistor_ad_channel = 0

    # create a/d converter
    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={thermistor_ad_channel: None}
    )

    # create thermistor on adc
    thermistor = Thermistor(
        adc=adc,
        channel=thermistor_ad_channel
    )

    try:
        while True:
            print(f'Degrees (F) : {thermistor.get_temperature_f():.1f}')
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass

    adc.close()
    cleanup()


if __name__ == '__main__':
    main()
