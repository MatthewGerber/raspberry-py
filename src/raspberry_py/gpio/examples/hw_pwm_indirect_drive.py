import time

from smbus2 import SMBus

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, Sg90DriverPCA9685PW


def main():
    """
    This example demonstrates the use of hardware pulse-wave modulation (PWM) to indirectly control a DC motor with the
    PWM output. It is designed for use with the PCA9685PW IC (see manuals/PCA9685.pdf) with a DC motor driver connected
    to the PWM output of channel 0.
    """

    setup()

    # set up pwm chip
    i2c_bus = SMBus('/dev/i2c-1')

    pca9685pw = PulseWaveModulatorPCA9685PW(
        bus=i2c_bus,
        address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS,
        frequency_hz=50
    )

    cleanup()


if __name__ == '__main__':
    main()
