import time
from enum import IntEnum
from threading import RLock, Thread, Lock
from typing import Optional, List, Union

from rpi_ws281x import Color
from smbus2 import SMBus

from raspberry_py.gpio import CkPin
from raspberry_py.gpio import Component
from raspberry_py.gpio.adc import ADS7830
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.lights import LedStrip
from raspberry_py.gpio.motors import DcMotor, DcMotorDriverPCA9685PW, Servo, Sg90DriverPCA9685PW
from raspberry_py.gpio.sensors import Camera, UltrasonicRangeFinder, MjpgStreamer
from raspberry_py.gpio.sounds import ActiveBuzzer


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
    The Freenove 4WD Smart Car. See manuals/freenove-awd-smart-car.pdf for details.

    TODO:
      * WiFi connection/display via LCD and keypad
      * Potentiometer input for light tracking gain
      * Connectivity via LTE:  Reverse tunneling
      * Image overlay:  Guide lines
      * RLAI
      * Left/right light tracking
      * Line tracking
    """

    class State(Component.State):
        """
        Car state.
        """

        def __init__(
                self,
                on: bool
        ):
            """
            Initialize the state.

            :param on: Whether the car is on.
            """

            self.on = on

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Car.State):
                raise ValueError(f'Expected a {Car.State}')

            return self.on == other.on

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'on={self.on}'

    def set_wheel_speed(
            self,
            wheels: List[DcMotor],
            speed: int
    ):
        """
        Set wheel speed.

        :param wheels: Wheels to change speed for.
        :param speed: Speed in [-100, 100].
        """

        with self.speed_lock:
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

        with self.speed_lock:
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

        with self.speed_lock:
            self.set_wheel_speed(self.left_wheels, speed)

    def set_right_speed(
            self,
            speed: int
    ):
        """
        Set the speed of the right wheels.

        :param speed: Speed in [-100,+100].
        """

        with self.speed_lock:
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

        with self.speed_lock:
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

        with self.on_off_lock:

            if self.on:
                return
            else:
                self.on = True

            for wheel in self.wheels:
                wheel.start()

            for servo in self.servos:
                servo.start()

            self.camera_tilt_servo.set_degrees(90)
            self.camera_pan_servo.set_degrees(90)
            self.camera.turn_on()

            # begin updating the A/D state
            self.update_analog_to_digital_state_thread = Thread(target=self.update_analog_to_digital_state)
            self.update_analog_to_digital_state_thread.start()

            # begin monitoring for connection blackout if specified
            if self.connection_blackout_tolerance_seconds is not None:
                self.previous_connection_heartbeat_time = time.time()
                self.monitor_connection_blackout_thread = Thread(target=self.monitor_connection_blackout)
                self.monitor_connection_blackout_thread.start()

            # create led strip. catch error in case permissions/capabilities are not set up for /dev/mem. do this here
            # instead of in constructor, so we can try again if permissions change.
            try:

                if self.led_strip is None:
                    self.led_strip = LedStrip(led_brightness=3)

                self.run_led_strip_thread = Thread(target=self.run_led_strip)
                self.run_led_strip_thread.start()

            except RuntimeError as e:
                if str(e) == 'ws2811_init failed with code -5 (mmap() failed)':
                    print('Failed to access /dev/mem for LED strip. Check README for solutions.')
                else:
                    raise e

            self.set_state(Car.State(on=True))

    def update_analog_to_digital_state(
            self
    ):
        """
        Update the A/D state while the car remains on.
        """

        while self.on:

            # ensure that the loop/thread doesn't die if updating the a/d state raises an exception, which can happen
            # if we're tracking light and the updated state sets differential speed, while a separate thread (from the
            # control screen) also sets the differential speed. we have a lock on the differential speed, but the two
            # updates probably happen in too close proximity.
            try:
                self.analog_to_digital.update_state()
            except Exception as e:
                print(f'Caught exception when attempting to update A/D state (ignoring):  {e}')

            time.sleep(0.5)

    def monitor_connection_blackout(
            self
    ):
        """
        Monitor connection blackout while the car remains on. Shut the car down if a connection heartbeat is not
        received within the blackout tolerance.
        """

        while self.on:

            with self.monitor_connection_blackout_lock:
                seconds_since_previous_heartbeat = time.time() - self.previous_connection_heartbeat_time
                if seconds_since_previous_heartbeat > self.connection_blackout_tolerance_seconds:
                    Thread(target=self.stop).start()
                    break

            # do not hold lock while sleeping
            time.sleep(self.connection_heartbeat_check_interval_seconds)

    def connection_heartbeat(
            self
    ):
        """
        Invoke a connection heartbeat.
        """

        with self.monitor_connection_blackout_lock:
            self.previous_connection_heartbeat_time = time.time()

    def run_led_strip(
            self
    ):
        """
        Run the LED strip while the car remains on.
        """

        while self.on:

            # ensure that the loop/thread doesn't die due to any strangeness in the underlying led api
            try:
                self.led_strip.theater_chase(Color(0, 255, 0), iterations=1, wait_ms=250)
            except Exception as e:
                print(f'Caught exception when running LED strip (ignoring):  {e}')

        self.led_strip.color_wipe(0, 0)

    def stop(
            self
    ):
        """
        Stop the car.
        """

        with self.on_off_lock:

            if self.on:
                self.on = False
            else:
                return

            for wheel in self.wheels:
                wheel.set_speed(0)
                wheel.stop()

            for servo in self.servos:
                servo.stop()

            self.camera.turn_off()

            if self.update_analog_to_digital_state_thread is not None:
                self.update_analog_to_digital_state_thread.join()
                self.update_analog_to_digital_state_thread = None

            if self.monitor_connection_blackout_thread is not None:
                self.monitor_connection_blackout_thread.join()
                self.monitor_connection_blackout_thread = None

            if self.run_led_strip_thread is not None:
                self.run_led_strip_thread.join()
                self.run_led_strip_thread = None

            self.set_state(Car.State(on=False))

    def get_components(
            self
    ) -> List[Component]:
        """
        Get a list of all GPIO circuit components in the car.

        :return: List of components.
        """

        self.wheels: List[Component]

        return self.wheels + self.servos + [self.buzzer, self.camera, self.range_finder]

    def track_detected_faces(
            self,
            detected_faces: List[Camera.DetectedFace]
    ):
        """
        Track detected faces.

        :param detected_faces: Detected faces.
        """

        if self.track_faces and len(detected_faces) == 1:

            detected_face = detected_faces[0]

            frame_width, frame_height = self.camera.get_frame_resolution()
            frame_middle_x = frame_width / 2.0
            frame_middle_y = frame_height / 2.0

            pan_delta = 0
            if detected_face.center_x > frame_middle_x + 10:
                pan_delta = 1.5
            elif detected_face.center_x < frame_middle_x - 10:
                pan_delta = -1.5

            if pan_delta != 0:
                self.camera_pan_servo.set_degrees(self.camera_pan_servo.get_degrees() + pan_delta)

            tilt_delta = 0
            if detected_face.center_y > frame_middle_y + 10:
                tilt_delta = -1.5
            elif detected_face.center_y < frame_middle_y - 10:
                tilt_delta = 1.5

            if tilt_delta != 0:
                self.camera_tilt_servo.set_degrees(self.camera_tilt_servo.get_degrees() + tilt_delta)

    def enable_face_tracking(
            self
    ):
        """
        Enable face tracking.
        """

        self.track_faces = True

    def disable_face_tracking(
            self
    ):
        """
        Disable face tracking.
        """

        self.track_faces = False

    def track_light_intensity(
            self,
            left: float,
            right: float
    ):
        """
        Track light intensity.

        :param left: Intensity of light on left side in [0.0,1.0].
        :param right: Intensity of light on right side in [0.0, 1.0].
        """

        if self.track_light:
            left_light_differential = self.light_difference_gain * (left - right)
            differential_speed = max(
                self.wheel_min_speed,
                min(
                    self.wheel_max_speed,
                    int(left_light_differential * self.wheel_max_speed)
                )
            )
            self.set_differential_speed(differential_speed)

    def enable_light_tracking(
            self
    ):
        """
        Enable light tracking.
        """

        self.track_light = True

    def disable_light_tracking(
            self
    ):
        """
        Disable light tracking.
        """

        self.track_light = False

    def get_battery_percent(
            self
    ) -> float:
        """
        Get battery percent.

        :return: Battery percent in [0,100].
        """

        voltage_percent = self.analog_to_digital.get_channel_value()[self.adc_battery_voltage_channel]

        if self.battery_min is not None and self.battery_max is not None:
            voltage_percent = 100.0 * min(
                1.0,
                max(
                    0.0,
                    (voltage_percent - self.battery_min) / (self.battery_max - self.battery_min)
                )
            )

        return voltage_percent

    def __init__(
            self,
            camera: Union[Camera, MjpgStreamer],
            camera_pan_servo_correction_degrees: float = 0.0,
            camera_tilt_servo_correction_degrees: float = 0.0,
            reverse_wheels: Optional[List[Wheel]] = None,
            min_speed: int = -100,
            max_speed: int = 100,
            connection_blackout_tolerance_seconds: Optional[float] = None,
            track_faces: bool = True,
            track_light: bool = False,
            battery_min: Optional[float] = None,
            battery_max: Optional[float] = None
    ):
        """
        Initialize the car.

        :param camera: Camera component.
        :param camera_pan_servo_correction_degrees: Pan correction. This number of degrees is added to any request to
        position the camera pan servo, in order to correct servo assembly errors. For example, the servo mount threading
        might not permit assembly at precisely the desired angle. If the servo is a few degrees one way or the other,
        add or subtract a few degrees here to get the desired mounting angle.
        :param camera_tilt_servo_correction_degrees: Tilt correction. This number of degrees is added to any request to
        position the camera tilt servo, in order to correct servo assembly errors. For example, the servo mount
        threading might not permit assembly at precisely the desired angle. If the servo is a few degrees one way or the
        other, add or subtract a few degrees here to get the desired mounting angle.
        :param reverse_wheels: List of wheels to reverse direction of, or None to reverse no wheels. Pass values here
        so that all positive wheel speeds move the car forward and all negative wheel speeds move the car backward.
        :param min_speed: Minimum speed in [-100,+100].
        :param max_speed: Maximum speed in [-100,+100].
        :param connection_blackout_tolerance_seconds: Maximum amount of time (seconds) to tolerate connection blackout,
        beyond which the car will automatically shut down. Pass None to not use this feature.
        :param track_faces: Whether to track detected faces. `run_face_detection` must be true for this to work.
        :param track_light: Whether to track light.
        :param battery_min: Battery rescaling minimum, or None to use raw voltage value.
        :param battery_max: Battery rescaling maximum, or None to use raw voltage value.
        """

        if (battery_min is None) != (battery_max is None):
            raise ValueError('The values of battery_min and battery_max must both be None or non-None.')

        if reverse_wheels is None:
            reverse_wheels = []

        super().__init__(Car.State(on=False))

        self.min_speed = min_speed
        self.max_speed = max_speed
        self.connection_blackout_tolerance_seconds = connection_blackout_tolerance_seconds
        self.track_faces = track_faces
        self.track_light = track_light
        self.battery_min = battery_min
        self.battery_max = battery_max

        self.light_difference_gain = 2.5

        self.on = False
        self.on_off_lock = Lock()

        self.i2c_bus = SMBus('/dev/i2c-1')

        # hardware pwm for motors/servos
        self.pwm = PulseWaveModulatorPCA9685PW(
            bus=self.i2c_bus,
            address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS,
            frequency_hz=50
        )

        # analog-to-digital converter
        self.adc_left_light_channel = 0
        self.adc_right_light_channel = 1
        self.adc_battery_voltage_channel = 2
        self.analog_to_digital = ADS7830(
            input_voltage=3.3,
            bus=self.i2c_bus,
            address=0x48,
            command=ADS7830.COMMAND,
            channel_rescaled_range={
                self.adc_left_light_channel: (0.0, 1.0),
                self.adc_right_light_channel: (0.0, 1.0),
                self.adc_battery_voltage_channel: (0.0, 100.0)
            }
        )

        # 4 wheel motors use PWM channels 0-7 (2 channels per motor)
        # noinspection PyTypeChecker
        self.wheels = [
            DcMotor(
                driver=DcMotorDriverPCA9685PW(
                    pca9685pw=self.pwm,
                    motor_channel_1=wheel.value * 2,
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
            driver=Sg90DriverPCA9685PW(
                pca9685pw=self.pwm,
                servo_channel=8,
                reverse=True,
                correction_degrees=camera_pan_servo_correction_degrees
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.camera_pan_servo.id = 'camera-pan'

        self.camera_tilt_servo = Servo(
            driver=Sg90DriverPCA9685PW(
                pca9685pw=self.pwm,
                servo_channel=9,
                correction_degrees=camera_tilt_servo_correction_degrees
            ),
            degrees=90.0,
            min_degree=85.0,  # don't permit tiling too low, as this will hit the servo mounts.
            max_degree=180.0
        )
        self.camera_tilt_servo.id = 'camera-tilt'

        self.servos = [
            self.camera_pan_servo,
            self.camera_tilt_servo
        ]

        # other components
        self.camera = camera
        if isinstance(self.camera, Camera):
            self.camera.face_detection_callback = self.track_detected_faces if self.track_faces else None
        elif not isinstance(self.camera, MjpgStreamer):
            raise ValueError(f'Unknown camera type:  {self.camera}')

        self.buzzer = ActiveBuzzer(CkPin.GPIO17)
        self.buzzer.id = 'buzzer'
        self.range_finder = UltrasonicRangeFinder(
            trigger_pin=CkPin.GPIO27,
            echo_pin=CkPin.GPIO22,
            measurements_per_second=1.0
        )
        self.range_finder.id = 'range_finder'

        # speed-differential turning
        self.speed_lock = RLock()
        self.current_all_wheel_speed = 0
        self.differential_speed = 0

        # track light intensity as the a/d state changes
        self.analog_to_digital.event(lambda s: self.track_light_intensity(
            left=s.channel_value[self.adc_left_light_channel],
            right=s.channel_value[self.adc_right_light_channel]
        ))
        self.update_analog_to_digital_state_thread = None

        # connection blackout
        self.monitor_connection_blackout_lock = Lock()
        self.monitor_connection_blackout_thread = None
        self.previous_connection_heartbeat_time = None
        self.connection_heartbeat_check_interval_seconds = self.connection_blackout_tolerance_seconds / 4.0

        # led strip
        self.led_strip = None
        self.run_led_strip_thread = None
