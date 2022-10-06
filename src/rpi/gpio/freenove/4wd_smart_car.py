from datetime import timedelta
from threading import Thread
from typing import Optional, List

from smbus2 import SMBus

from rpi.gpio import Component
from rpi.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from rpi.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, ServoDriverPCA9685PW


class Car(Component):

    class State(Component.State):

        def __eq__(self, other: object) -> bool:
            return False

        def __str__(self) -> str:
            return ''

    @staticmethod
    def set_absolute_wheel_speed(
            wheels: List[DcMotor],
            speed: int
    ):
        """
        Set an absolute wheel speed.

        :param wheels: Wheels to change speed for.
        :param speed: Speed in [-100, 100].
        """

        for wheel in wheels:
            wheel.set_speed(speed)

    def set_fractional_wheel_speed(
            self,
            wheels: List[DcMotor],
            speed_fraction: float,
            duration: Optional[timedelta] = None,
            async_duration: bool = False
    ):
        """
        Set a temporary wheelspeed change.

        :param wheels: Wheels to change speed for.
        :param speed_fraction: Fraction of speed to retain in the wheels.
        :param duration: Duration of time to retain the speed change before returning to the current speed, or None
        to retain the speed change indefinitely.
        :param async_duration: If duration is not None, this is whether the wait should be asynchronous. If it is
        asynchronous, then the function call will return immediately and wait in a thread.
        """

        for wheel in wheels:
            wheel.set_speed(int(wheel.get_speed() * speed_fraction))

        if duration is not None:
            if async_duration:
                Thread(target=lambda: self.set_fractional_wheel_speed(wheels, 1.0 + speed_fraction, None, False)).start()
            else:
                self.set_fractional_wheel_speed(wheels, 1.0 + speed_fraction, None, False)

    def zero_move_turn(
            self,
            speed: int,
            duration
    ):
        pass

    def __init__(
            self
    ):
        """
        Initialize the car
        """

        super().__init__(Car.State())

        i2c_bus = SMBus('/dev/i2c-1')

        pca9685pw = PulseWaveModulatorPCA9685PW(
            bus=i2c_bus,
            address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS
        )
        pca9685pw.set_pwm_frequency(50)

        # 4 wheel motors use PWM channels 0-7 (2 channels per motor)
        self.wheels = [
            DcMotor(
                driver=DcMotorDriverPCA9685PW(
                    pca9685pw=pca9685pw,
                    motor_channel_1=motor_channel_1,
                    motor_channel_2=motor_channel_2
                ),
                speed=0
            )
            for motor_channel_1, motor_channel_2 in [(0, 1), (2, 3), (4, 5), (6, 7)]
        ]
        (
            self.front_left_wheel,
            self.rear_left_wheel,
            self.rear_right_wheel,
            self.front_right_wheel
        ) = self.wheels
        self.left_wheels = [self.front_left_wheel, self.rear_left_wheel]
        self.right_wheels = [self.front_right_wheel, self.rear_right_wheel]
        self.front_wheels = [self.front_left_wheel, self.front_right_wheel]
        self.rear_wheels = [self.rear_left_wheel, self.rear_right_wheel]

        # 8 servos use PWM channels 8-15 (1 channel per servo)
        self.servos = [
            Servo(
                driver=ServoDriverPCA9685PW(
                    pca9685pw=pca9685pw,
                    servo_channel=servo_channel
                ),
                degrees=90
            )
            for servo_channel in range(8, 16)
        ]
        (
            self.camera_pan_servo,
            self.camera_tilt_servo
        ) = self.servos[0:2]
