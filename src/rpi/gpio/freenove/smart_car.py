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
        Set a temporary wheel speed change.

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

    def stationary_turn(
            self,
            speed: int,
            duration
    ):
        """
        Conduct a stationary turn by moving left- and right-side wheels in opposite directions.

        :param speed: Wheel speed.
        :param duration: Duration of time to execute the turn.
        """
        pass

    def start(
            self
    ):
        """
        Start the car.
        """

        for wheel in self.wheels:
            wheel.start()

        for servo in self.servos:
            servo.start()

    def stop(
            self
    ):
        """
        Stop the car.
        """

        for wheel in self.wheels:
            wheel.stop()

        for servo in self.servos:
            servo.stop()

    def __init__(
            self,
            camera_pan_servo_correction_degrees: float = 0.0,
            camera_tilt_servo_correction_degrees: float = 0.0,
            reverse_wheels: Optional[List[int]] = None
    ):
        """
        Initialize the car.

        :param camera_pan_servo_correction_degrees: Pan correction.
        :param camera_tilt_servo_correction_degrees: Tilt correction.
        :param reverse_wheels: List of wheel numbers to reverse direction of, or None to reverse no wheels. Wheels are
        numbered as follows:  (0) front left, (1) rear left, (2) rear right, and (3) front right.
        """

        if reverse_wheels is None:
            reverse_wheels = []

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
                    motor_channel_2=motor_channel_2,
                    reverse=i in reverse_wheels
                ),
                speed=0
            )
            for i, (motor_channel_1, motor_channel_2) in enumerate([(0, 1), (2, 3), (4, 5), (6, 7)])
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
        self.camera_pan_servo = Servo(
            driver=ServoDriverPCA9685PW(
                pca9685pw=pca9685pw,
                servo_channel=8,
                reverse=False,
                correction_degrees=camera_pan_servo_correction_degrees
            ),
            degrees=90,
            min_degree=0,
            max_degree=180
        )

        self.camera_tilt_servo = Servo(
            driver=ServoDriverPCA9685PW(
                pca9685pw=pca9685pw,
                servo_channel=9,
                reverse=True,  # the tilt servo is mounted in reverse, such that 180 points up.
                correction_degrees=camera_tilt_servo_correction_degrees
            ),
            degrees=90,
            min_degree=75,  # don't permit tiling too low, as this will hit the servo mounts.
            max_degree=180
        )

        self.servos = [
            self.camera_pan_servo,
            self.camera_tilt_servo
        ]