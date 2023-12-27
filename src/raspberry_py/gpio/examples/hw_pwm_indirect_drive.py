import time

from smbus2 import SMBus

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import DcMotor, DcMotorDriverIndirectPCA9685PW


def main():
    """
    This example demonstrates the use of hardware pulse-wave modulation (PWM) to indirectly control a DC motor with the
    PWM output. It is designed for use with the PCA9685PW IC (see manuals/PCA9685.pdf) and a DC motor driver connected
    to the PWM output of channel 0.
    """

    setup()

    # set up pwm chip
    pca9685pw = PulseWaveModulatorPCA9685PW(
        bus=SMBus('/dev/i2c-1'),
        address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS,
        frequency_hz=400
    )

    # test motor
    motor = DcMotor(
        driver=DcMotorDriverIndirectPCA9685PW(
            pca9685pw=pca9685pw,
            pwm_channel=0,
            direction_pin=CkPin.GPIO21
        ),
        speed=0
    )
    motor.start()
    motor.set_speed(50)
    time.sleep(1)
    motor.set_speed(-50)
    time.sleep(1)
    motor.set_speed(0)
    motor.stop()

    cleanup()


if __name__ == '__main__':
    main()
