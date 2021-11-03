import math
import time

from smbus2 import SMBus

from rpi.gpio.adc import ADS7830


def main():
    """
    This example displays the value of a thermistor via an analog-to-digital converter, as shown on page 145 of the
    tutorial.
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
            Rt = 10 * voltage / (3.3 - voltage)
            temp_k = 1 / (1 / (273.15 + 25) + math.log(Rt / 10) / 3950.0)
            temp_c = temp_k - 273.15
            temp_f = temp_c * (9.0/5.0) + 32.0
            print(f'ADC Value: {value}, Degrees (F) : {temp_f:.2f}')
            time.sleep(0.1)
    except KeyboardInterrupt:
        adc.close()


if __name__ == '__main__':
    main()
