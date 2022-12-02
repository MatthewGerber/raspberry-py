import time

from smbus2 import SMBus

from raspberry_py.gpio import cleanup
from raspberry_py.gpio.adc import ADS7830


def main():
    """
    This example displays the value of an analog component (e.g., potentiometer) via an analog-to-digital converter, as
    shown on page 115 of the tutorial.
    """

    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={0: None}
    )

    try:
        while True:
            digital_value = adc.analog_read(0)
            voltage = adc.get_voltage(digital_value)
            print(f'ADC Value: {digital_value}, Voltage : {voltage:.2f}')
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

    adc.close()
    cleanup()


if __name__ == '__main__':
    main()
