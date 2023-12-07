import time

from smbus2 import SMBus

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, Sg90DriverPCA9685PW


def main():
    """
    This example demonstrates the use of hardware pulse-wave modulation (PWM) to directly control motors with the PWM
    output. It is designed for use with the PCA9685PW IC (see manuals/PCA9685.pdf) with a DcMotor attached to PWM output
    channels 0 and 1 and a Servo attached to PWM output channel 8. This is the setup used in the Freenove SmartCar;
    however, nothing about this example is specific to that application beyond the channel connections.
    """

    setup()

    # set up pwm chip
    pca9685pw = PulseWaveModulatorPCA9685PW(
        bus=SMBus('/dev/i2c-1'),
        address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS,
        frequency_hz=50
    )

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
        driver=Sg90DriverPCA9685PW(
            pca9685pw=pca9685pw,
            servo_channel=8
        ),
        degrees=0.0,
        min_degree=0.0,
        max_degree=180.0
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
