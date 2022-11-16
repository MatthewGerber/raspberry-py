import time
from datetime import timedelta
from enum import IntEnum
from threading import RLock, Thread
from typing import Optional, List

from smbus2 import SMBus

from rpi.gpio import CkPin
from rpi.gpio import Component
from rpi.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from rpi.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, ServoDriverPCA9685PW
from rpi.gpio.sensors import Camera, UltrasonicRangeFinder
from rpi.gpio.sounds import ActiveBuzzer


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
    def set_wheel_speed(
            wheels: List[DcMotor],
            speed: int
    ):
        """
        Set wheel speed.

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
            if self.differential_speed != 0:
                self.set_differential_speed(self.differential_speed)
            else:
                self.set_wheel_speed(self.wheels, speed)

    def set_left_speed(
            self,
            speed: int
    ):
        """
        Set the speed of the left wheels.

        :param speed: Speed in [-100,+100].
        """

        self.set_wheel_speed(self.left_wheels, speed)

    def set_right_speed(
            self,
            speed: int
    ):
        """
        Set the speed of the right wheels.

        :param speed: Speed in [-100,+100].
        """

        self.set_wheel_speed(self.right_wheels, speed)

    def set_differential_speed(
            self,
            differential_speed: int
    ):
        """
        Set a differential speed of the left and right wheels.

        :param differential_speed: Differential speed to apply to the current speed. When the car is moving forward,
        positive values cause the right wheels to spin faster than the left, and vice versa for negative values. When
        the car if moving backward, negative values make the right wheels spin faster than the left.
        """

        with self.speed_differential_lock:
            self.differential_speed = differential_speed
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

        # begin monitoring the safety heartbeat if specified
        with self.safety_heartbeat_lock:
            if self.safety_heartbeat_tolerance_seconds is not None:
                self.stop_safety_heartbeat_monitor()
                self.continue_safety_heartbeat_monitor = True
                self.previous_heartbeat_time = time.time()
                self.monitor_safety_heartbeat_thread = Thread(target=self.monitor_safety_heartbeat)
                self.monitor_safety_heartbeat_thread.start()

    def monitor_safety_heartbeat(
            self
    ):
        """
        Shut the car down if a safety heartbeat is not received within the tolerated time.
        """

        while True:

            with self.safety_heartbeat_lock:
                if self.continue_safety_heartbeat_monitor:
                    seconds_since_previous_heartbeat = time.time() - self.previous_heartbeat_time
                    if seconds_since_previous_heartbeat > self.safety_heartbeat_tolerance_seconds:
                        Thread(target=self.stop).start()
                        self.continue_safety_heartbeat_monitor = False
                else:
                    break

            time.sleep(self.safety_heartbeat_check_interval_seconds)

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

        self.camera_tilt_servo.set_degrees(90)
        self.camera_pan_servo.set_degrees(90)

        self.stop_safety_heartbeat_monitor()

    def stop_safety_heartbeat_monitor(
            self
    ):
        """
        Stop the safety heartbeat monitor.
        """

        with self.safety_heartbeat_lock:
            if self.monitor_safety_heartbeat_thread is not None:
                self.continue_safety_heartbeat_monitor = False
                self.monitor_safety_heartbeat_thread.join()
                self.monitor_safety_heartbeat_thread = None

    def safety_heartbeat(
            self
    ):
        """
        Invoke the safety heartbeat.
        """

        with self.safety_heartbeat_lock:
            self.previous_heartbeat_time = time.time()

    def get_components(
            self
    ) -> List[Component]:
        """
        Get a list of all GPIO circuit components in the car.

        :return: List of components.
        """

        self.wheels: List[Component]

        return self.wheels + self.servos + [self.buzzer, self.camera, self.range_finder]

    def __init__(
            self,
            camera_pan_servo_correction_degrees: float = 0.0,
            camera_tilt_servo_correction_degrees: float = 0.0,
            reverse_wheels: Optional[List[Wheel]] = None,
            camera_device: str = '/dev/video0',
            camera_width: int = 640,
            camera_height: int = 480,
            camera_fps: int = 30,
            min_speed: int = -100,
            max_speed: int = 100,
            safety_heartbeat_tolerance_seconds: Optional[float] = None
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
        :param safety_heartbeat_tolerance_seconds: Maximum amount of time (seconds) to tolerate the absence of a safety
        heartbeat signal, beyond with the car will automatically shut down. Pass None to not use the safety heartbeat.
        """

        if reverse_wheels is None:
            reverse_wheels = []

        super().__init__(Car.State())

        self.min_speed = min_speed
        self.max_speed = max_speed
        self.safety_heartbeat_tolerance_seconds = safety_heartbeat_tolerance_seconds

        # hardware pwm for motors/servos
        i2c_bus = SMBus('/dev/i2c-1')
        pca9685pw = PulseWaveModulatorPCA9685PW(
            bus=i2c_bus,
            address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS
        )
        pca9685pw.set_pwm_frequency(50)

        # wheels
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
            min_degree=80,  # don't permit tiling too low, as this will hit the servo mounts.
            max_degree=180
        )
        self.camera_tilt_servo.id = 'camera-tilt'

        self.servos = [
            self.camera_pan_servo,
            self.camera_tilt_servo
        ]

        # other components
        self.camera = Camera(
            device=camera_device,
            width=camera_width,
            height=camera_height,
            fps=camera_fps
        )
        self.camera.id = 'camera'
        self.buzzer = ActiveBuzzer(CkPin.GPIO17)
        self.buzzer.id = 'buzzer'
        self.range_finder = UltrasonicRangeFinder(
            trigger_pin=CkPin.GPIO27,
            echo_pin=CkPin.GPIO22,
            measurements_per_second=1.0
        )
        self.range_finder.id = 'range_finder'

        # attributes for speed-differential turning
        self.speed_differential_lock = RLock()
        self.current_all_wheel_speed = 0
        self.differential_speed = 0

        # safety heartbeat thread
        self.monitor_safety_heartbeat_thread = None
        self.continue_safety_heartbeat_monitor = False
        self.previous_heartbeat_time = None
        self.safety_heartbeat_lock = RLock()
        self.safety_heartbeat_check_interval_seconds = 0.1
