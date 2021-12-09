import time

from smbus2 import SMBus

from rpi.gpio import setup, CkPin, cleanup
from rpi.gpio.adc import ADS7830
from rpi.gpio.motors import DcMotor


def main():
    """
    This example drives a DC motor as shown on page 164 of the tutorial.
    """

    setup()

    adc = ADS7830(
        input_voltage=3.3,
        bus=SMBus('/dev/i2c-1'),
        address=ADS7830.ADDRESS,
        command=ADS7830.COMMAND,
        channel_rescaled_range={0: (-100, 100)}
    )

    dc_motor = DcMotor(
        enable_pin=CkPin.GPIO22,
        in_1_pin=CkPin.GPIO27,
        in_2_pin=CkPin.GPIO17
    )

    dc_motor.start()
    adc.event(lambda s: dc_motor.set_speed(s.channel_value[0]))

    try:
        while True:
            adc.update_state()
            time.sleep(0.5)
    except KeyboardInterrupt:
        dc_motor.stop()
        adc.close()
        cleanup()


if __name__ == '__main__':
    main()
