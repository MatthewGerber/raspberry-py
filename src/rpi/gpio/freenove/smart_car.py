from datetime import timedelta
from enum import IntEnum
from threading import RLock
from typing import Optional, List

from smbus2 import SMBus

from rpi.gpio import Component
from rpi.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from rpi.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, ServoDriverPCA9685PW
from rpi.gpio.sensors import Camera


class Wheel(IntEnum):
    """
    Wheels.
    """

    FRONT_LEFT = 0
    REAR_LEFT = 1
    REAR_RIGHT = 2
    FRONT_RIGHT = 3


class Car(Component):
    """
    The Freenove 4WD Smart Car.
    """

    class State(Component.State):
        """
        Car state. Currently not used.
        """

        def __eq__(self, other: object) -> bool:
            """
            Check equality with another state.
            """

            return False

        def __str__(self) -> str:
            """
            Get string.

            :return: String.
            """

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

    def set_speed(
            self,
            speed: int
    ):
        """
        Set the speed of all wheels.

        :param speed: Speed in [-100,+100].
        """

        with self.speed_differential_lock:

            self.current_all_wheel_speed = speed

            # only set differential speed for positive speeds
            if self.current_all_wheel_speed > 0 and self.differential_speed != 0:
                self.set_speed_differential(self.differential_speed)

            # otherwise, set speed of all wheels.
            else:
                self.set_absolute_wheel_speed(self.wheels, speed)

    def set_left_speed(
            self,
            speed: int
    ):
        """
        Set the speed of the left wheels.

        :param speed: Speed in [-100,+100].
        """

        self.set_absolute_wheel_speed(self.left_wheels, speed)

    def set_right_speed(
            self,
            speed: int
    ):
        """
        Set the speed of the right wheels.

        :param speed: Speed in [-100,+100].
        """

        self.set_absolute_wheel_speed(self.right_wheels, speed)

    def set_speed_differential(
            self,
            differential_speed: int
    ):
        """
        Set the speed differential of the left and right wheels.

        :param differential_speed: Differential speed to apply to the current speed, in [-200,+200]. Only has an effect
        when the current speed is positive. Positive values cause the right wheels to spin faster than the left, and
        vice versa for negative values.
        """

        with self.speed_differential_lock:

            self.differential_speed = differential_speed

            if self.current_all_wheel_speed < 0:
                return

            left_speed = self.current_all_wheel_speed - self.differential_speed
            left_speed = max(self.wheel_min_speed, min(self.wheel_max_speed, left_speed))
            right_speed = self.current_all_wheel_speed + self.differential_speed
            right_speed = max(self.wheel_min_speed, min(self.wheel_max_speed, right_speed))

            self.set_left_speed(left_speed)
            self.set_right_speed(right_speed)

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

        # signal start
        self.camera_tilt_servo.set_degrees(90)
        self.camera_pan_servo.set_degrees(70, timedelta(seconds=1))
        self.camera_pan_servo.set_degrees(110, timedelta(seconds=1))
        self.camera_pan_servo.set_degrees(90, timedelta(seconds=0.5))

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

    def get_components(
            self
    ) -> List[Component]:
        """
        Get a list of all GPIO circuit components in the car.

        :return: List of components.
        """

        self.wheels: List[Component]

        return self.wheels + self.servos + [self.camera]

    def __init__(
            self,
            camera_pan_servo_correction_degrees: float = 0.0,
            camera_tilt_servo_correction_degrees: float = 0.0,
            reverse_wheels: Optional[List[Wheel]] = None,
            camera_device: str = '/dev/video0',
            camera_width: int = 640,
            camera_height: int = 480,
            camera_fps: int = 30,
            min_speed=-100,
            max_speed=100
    ):
        """
        Initialize the car.

        :param camera_pan_servo_correction_degrees: Pan correction. This number of degrees is added to any request to
        position the camera pan servo, in order to correct servo assembly errors. For example, the servo threading
        might not permit assembly at the desired angle. If the servo is a few degrees one way or the other, add or
        subtract a few degrees here to get the desired angle.
        :param camera_tilt_servo_correction_degrees: Tilt correction. This number of degrees is added to any request to
        position the camera tilt servo, in order to correct servo assembly errors. For example, the servo threading
        might not permit assembly at the desired angle. If the servo is a few degrees one way or the other, add or
        subtract a few degrees here to get the desired angle.
        :param reverse_wheels: List of wheels to reverse direction of, or None to reverse no wheels. Pass values here
        so that all positive wheel speeds move the car forward and all negative wheel speeds move the car backward.
        :param camera_device: Camera device.
        :param camera_width: Camera image width.
        :param camera_height: Camera image height.
        :param camera_fps: Camera frames per second.
        :param min_speed: Minimum speed in [-100,+100].
        :param max_speed: Maximum speed in [-100,+100].
        """

        if reverse_wheels is None:
            reverse_wheels = []

        super().__init__(Car.State())

        self.min_speed = min_speed
        self.max_speed = max_speed

        i2c_bus = SMBus('/dev/i2c-1')

        pca9685pw = PulseWaveModulatorPCA9685PW(
            bus=i2c_bus,
            address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS
        )
        pca9685pw.set_pwm_frequency(50)

        self.wheels = [
            DcMotor(
                driver=DcMotorDriverPCA9685PW(
                    pca9685pw=pca9685pw,
                    motor_channel_1=wheel.value * 2,  # 4 wheel motors use PWM channels 0-7 (2 channels per motor)
                    motor_channel_2=wheel.value * 2 + 1,
                    reverse=wheel in reverse_wheels
                ),
                speed=0
            )
            for wheel in Wheel
        ]
        self.wheel_min_speed, self.wheel_max_speed = self.wheels[0].min_speed, self.wheels[0].max_speed
        for wheel, wheel_id in zip(self.wheels, Wheel):
            wheel.id = f'wheel-{wheel_id.name.lower().replace("_", "-")}'
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
        self.camera_pan_servo.id = 'camera-pan'

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
        self.camera_tilt_servo.id = 'camera-tilt'

        self.servos = [
            self.camera_pan_servo,
            self.camera_tilt_servo
        ]

        self.camera = Camera(
            device=camera_device,
            width=camera_width,
            height=camera_height,
            fps=camera_fps
        )
        self.camera.id = 'camera'

        self.speed_differential_lock = RLock()
        self.current_all_wheel_speed = 0
        self.differential_speed = 0
