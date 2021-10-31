import time

from rpi.gpio.adc import AdcDevice


def main():
    """
    This example displays the value of a potentiometer via an analog-to-digital converter, as shown on page 115 of the
    tutorial.
    """

    adc = AdcDevice.detect_i2c('/dev/i2c-1', {0: None})

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
