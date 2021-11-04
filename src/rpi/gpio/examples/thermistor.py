import time

from smbus2 import SMBus

from rpi.gpio.adc import ADS7830
from rpi.gpio.sensors import Thermistor


def main():
    """
    This example displays the value of a thermistor via an analog-to-digital converter, as shown on page 145 of the
    tutorial.
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
            value = adc.analog_read(0)
            voltage = adc.get_voltage(value)
            temp_f = Thermistor.get_temperature(voltage, adc.input_voltage)
            print(f'ADC Value: {value}, Degrees (F) : {temp_f:.2f}')
            time.sleep(0.1)
    except KeyboardInterrupt:
        adc.close()


if __name__ == '__main__':
    main()
