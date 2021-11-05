import logging
import time

from smbus2 import SMBus

from rpi.gpio import setup, CkPin, cleanup
from rpi.gpio.adc import ADS7830
from rpi.gpio.lights import LedBar
from rpi.gpio.sensors import Thermistor


def main():
    """
    This example displays the value of a thermistor via an analog-to-digital converter, as shown on page 145 of the
    tutorial.
    """

    setup()

    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={0: None}
    )

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

    num_leds = len(led_bar.leds)
    temp_display_low_f = 70.0
    temp_display_high_f = 85.0
    temp_display_range_f = temp_display_high_f - temp_display_low_f
    led_bar.turn_off()
    leds_to_illuminate = None
    logging.getLogger().setLevel(logging.INFO)
    try:
        while True:
            value = adc.analog_read(0)
            voltage = adc.get_voltage(value)
            temp_f = Thermistor.get_temperature(voltage, adc.input_voltage)
            new_leds_to_illuminate = int(num_leds * (temp_f - temp_display_low_f) / temp_display_range_f)
            new_leds_to_illuminate = max(0, new_leds_to_illuminate)
            new_leds_to_illuminate = min(num_leds, new_leds_to_illuminate)
            if leds_to_illuminate is None or leds_to_illuminate != new_leds_to_illuminate:
                logging.info(f'Temp: {temp_f}, LEDs: {new_leds_to_illuminate}')
                leds_to_illuminate = new_leds_to_illuminate
                led_bar.turn_off()
                led_bar.turn_on(list(range(0, leds_to_illuminate)))
            time.sleep(0.5)
    except KeyboardInterrupt:
        adc.close()
        led_bar.turn_off()
        cleanup()


if __name__ == '__main__':
    main()
