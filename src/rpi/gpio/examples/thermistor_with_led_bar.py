import logging
import time

from smbus2 import SMBus

from rpi.gpio import setup, CkPin, cleanup
from rpi.gpio.adc import ADS7830
from rpi.gpio.lights import LedBar
from rpi.gpio.sensors import Thermistor


def main():
    """
    This example displays the value of a thermistor on an LED bar. The thermistor is read via analog-to-digital
    converter, as shown on page 145 of the tutorial.
    """

    setup()

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

    # create led bar
    led_bar = LedBar(
        output_pins=[
            CkPin.GPIO17,
            CkPin.GPIO18,
            CkPin.GPIO27,
            CkPin.GPIO22,
            CkPin.GPIO23,
            CkPin.GPIO24,
            CkPin.GPIO21,
            CkPin.GPIO20,
            CkPin.GPIO26,
            CkPin.GPIO12
        ],
        reverse=True
    )
    led_bar.turn_off()

    # set display range
    num_leds = len(led_bar)
    temp_low_f = 70.0
    temp_high_f = 98.6
    temp_range_f = temp_high_f - temp_low_f
    num_leds_on = None

    # define function to update number of leds illuminated on the bar
    def update_led_bar(
            temp_f: float
    ):
        """
        Update the LED bar based on new temperature.

        :param temp_f: New temperature.
        """

        nonlocal num_leds_on

        frac_temp_range = (temp_f - temp_low_f) / temp_range_f
        new_num_leds_on = min(num_leds, max(0, int(num_leds * frac_temp_range)))
        if num_leds_on is None or num_leds_on != new_num_leds_on:
            logging.info(f'Temp: {temp_f}, LEDs: {new_num_leds_on}')
            num_leds_on = new_num_leds_on
            led_bar.turn_off()
            led_bar.turn_on(list(range(0, num_leds_on)))

    # update the led bar when the temperature changes
    thermistor.event(lambda s: update_led_bar(s.temperature_f))

    # update the adc
    try:
        while True:
            adc.update_state()
            time.sleep(0.25)
    except KeyboardInterrupt:
        adc.close()
        led_bar.turn_off()
        cleanup()


if __name__ == '__main__':
    main()
