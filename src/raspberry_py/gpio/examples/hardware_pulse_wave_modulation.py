import time

from smbus2 import SMBus

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, ServoDriverPCA9685PW


def main():
    """
    This example demonstrates the use of hardware pulse-wave modulation. It is designed for use with the Freenove 4WD
    Smart Car.
    """

    setup()

    # set up pwm chip
    i2c_bus = SMBus('/dev/i2c-1')

    pca9685pw = PulseWaveModulatorPCA9685PW(
        bus=i2c_bus,
        address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS
    )
    pca9685pw.set_pwm_frequency(50)

    # test motor
    motor = DcMotor(
        driver=DcMotorDriverPCA9685PW(
            pca9685pw=pca9685pw,
            motor_channel_1=0,
            motor_channel_2=1
        ),
        speed=0
    )
    motor.start()
    motor.set_speed(75)
    time.sleep(1)
    motor.set_speed(-75)
    time.sleep(1)
    motor.set_speed(0)
    motor.stop()

    # test servo
    servo = Servo(
        driver=ServoDriverPCA9685PW(
            pca9685pw=pca9685pw,
            servo_channel=8
        ),
        degrees=0,
    )
    servo.start()
    time.sleep(1)
    servo.set_degrees(90)
    time.sleep(1)
    servo.set_degrees(180)
    time.sleep(1)
    servo.set_degrees(0)
    time.sleep(1)
    servo.stop()

    cleanup()


if __name__ == '__main__':
    main()
