import time

from rpi.gpio.adc import ADS7830
from smbus2 import SMBus


def main():
    """
    This example displays the value of an analog component (e.g., potentiometer) via an analog-to-digital converter, as
    shown on page 115 of the tutorial.
    """

    adc = ADS7830(
        SMBus('/dev/i2c-1'),
        ADS7830.COMMAND,
        ADS7830.ADDRESS,
        {0: None}
    )

    try:
        while True:
            value = adc.analog_read(0)
            voltage = value / 255.0 * 3.3
            print(f'ADC Value: {value}, Voltage : {voltage:.2f}')
            time.sleep(0.1)
    except KeyboardInterrupt:
        adc.close()


if __name__ == '__main__':
    main()
