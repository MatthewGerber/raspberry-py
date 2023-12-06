import base64
import math
import os
import shlex
import signal
import subprocess
import time
from enum import Enum, auto
from threading import Thread, Lock
from typing import Optional, List, Callable, Tuple

import RPi.GPIO as gpio
import cv2
import numpy as np

from raspberry_py.gpio import Component, CkPin
from raspberry_py.gpio.adc import AdcDevice
from raspberry_py.gpio.controls import TwoPoleButton


class Photoresistor(Component):
    """
    Photoresistor, to be connected via ADC.
    """

    class State(Component.State):
        """
        Photoresistor state.
        """

        def __init__(
                self,
                light_level: Optional[float]
        ):
            """
            Initialize the state.

            :param light_level: Light level (0-100, unitless).
            """

            self.light_level = light_level

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Photoresistor.State):
                raise ValueError(f'Expected a {Photoresistor.State}')

            return self.light_level == other.light_level

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return str(self.light_level)

    def update_state(
            self
    ):
        """
        Update state.
        """

        self.adc.update_state()

    def get_light_level(
            self
    ) -> float:
        """
        Get light level.

        :return: Light level.
        """

        self.adc.update_state()

        state: Photoresistor.State = self.state

        return state.light_level

    def __init__(
            self,
            adc: AdcDevice,
            channel: int
    ):
        """
        Initialize the photoresistor.

        :param adc: Analog-to-digital converter.
        :param channel: Analog-to-digital channel on which to monitor values from the photoresistor.
        """

        super().__init__(Photoresistor.State(light_level=None))

        self.adc = adc
        self.channel = channel

        # listen for events from the adc and update light level when they occur
        self.adc.event(
            lambda s: self.set_state(
                Photoresistor.State(
                    light_level=s.channel_value[self.channel]
                )
            )
        )


class Thermistor(Component):
    """
    Thermistor, to be connected via ADC.
    """

    class State(Component.State):
        """
        Thermistor state.
        """

        def __init__(
                self,
                temperature_f: Optional[float]
        ):
            """
            Initialize the state.

            :param temperature_f: Temperature (F).
            """

            self.temperature_f = temperature_f

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Thermistor.State):
                raise ValueError(f'Expected a {Thermistor.State}')

            return self.temperature_f == other.temperature_f

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'{self.temperature_f} (F)'

    @staticmethod
    def convert_voltage_to_temperature(
            input_voltage: float,
            output_voltage: float
    ) -> float:
        """
        Convert voltage to temperature.

        :param input_voltage: Input voltage to thermistor.
        :param output_voltage: Output voltage from thermistor.
        :return: Temperature (F).
        """

        rt = 10.0 * output_voltage / (input_voltage - output_voltage)
        temp_k = 1 / (1 / (273.15 + 25) + math.log(rt / 10.0) / 3950.0)
        temp_c = temp_k - 273.15
        temp_f = temp_c * (9.0 / 5.0) + 32.0

        return temp_f

    def update_state(
            self
    ):
        """
        Update state.
        """

        self.adc.update_state()

    def get_temperature_f(
            self
    ) -> float:
        """
        Get temperature (F).

        :return: Temperature (F).
        """

        self.adc.update_state()

        state: Thermistor.State = self.state

        return state.temperature_f

    def __init__(
            self,
            adc: AdcDevice,
            channel: int
    ):
        """
        Initialize the thermistor.

        :param adc: Analog-to-digital converter.
        :param channel: Analog-to-digital channel on which to monitor values from the thermistor.
        """

        super().__init__(Thermistor.State(temperature_f=None))

        self.adc = adc
        self.channel = channel

        # listen for events from the adc and update temperature when they occur
        self.adc.event(
            lambda s: self.set_state(
                Thermistor.State(
                    temperature_f=self.convert_voltage_to_temperature(
                        input_voltage=self.adc.input_voltage,
                        output_voltage=adc.get_voltage(
                            digital_output=s.channel_value[self.channel]
                        )
                    )
                )
            )
        )


class Hygrothermograph(Component):
    """
    Hygrothermograph (DHT11).
    """

    class State(Component.State):
        """
        Hygrothermograph state.
        """

        # noinspection PyArgumentList
        class Status(Enum):
            """
            State statuses.
            """

            OK = auto()
            CHECKSUM_ERROR = auto()
            TIMEOUT_ERROR = auto()
            INVALID_VALUE = auto()

        def __init__(
                self,
                temperature_f: Optional[float],
                humidity: Optional[float],
                status: Status
        ):
            """
            Initialize the state.

            :param temperature_f: Temperature (F).
            :param humidity: Humidity.
            :param status: Status.
            """

            self.temperature_f = temperature_f
            self.humidity = humidity
            self.status = status

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Hygrothermograph.State):
                raise ValueError(f'Expected a {Hygrothermograph.State}')

            return self.temperature_f == other.temperature_f and self.humidity == other.humidity and self.status == other.status

        def __str__(self) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Temp (F):  {self.temperature_f} (F), Humidity:  {self.humidity}, Status:  {self.status}'

    WAKEUP_SECS = 0.02
    TIMEOUT_SECS = 0.0001  # 100us
    BIT_HIGH_TIME_THRESHOLD_SECS = 0.00005

    def __init__(
            self,
            pin: int
    ):
        """
        Initialize the hygrothermograph.

        :param pin: GPIO pin connected to the SDA port of the hygrothermograph.
        """

        super().__init__(Hygrothermograph.State(None, None, Hygrothermograph.State.Status.INVALID_VALUE))

        self.pin = pin

        self.bytes = [0, 0, 0, 0, 0]

    def read(
            self,
            num_attempts: int = 1
    ):
        """
        Read the sensor.

        :param num_attempts: Number of attempts.
        """

        for _ in range(0, num_attempts):
            if self.__read_bytes__():
                humidity = self.bytes[0] + self.bytes[1] * 0.1
                temperature_c = self.bytes[2] + self.bytes[3] * 0.1
                temperature_f = temperature_c * 9.0/5.0 + 32.0
                checksum = (self.bytes[0] + self.bytes[1] + self.bytes[2] + self.bytes[3]) & 0xFF  # only retain the lowest 8 bits
                if self.bytes[4] == checksum:
                    state = Hygrothermograph.State(temperature_f, humidity, Hygrothermograph.State.Status.OK)
                else:
                    state = Hygrothermograph.State(None, None, Hygrothermograph.State.Status.CHECKSUM_ERROR)
            else:
                state = Hygrothermograph.State(None, None, Hygrothermograph.State.Status.TIMEOUT_ERROR)

            self.set_state(state)

            if state.status == Hygrothermograph.State.Status.OK:
                break
            else:
                time.sleep(0.1)

    def __read_bytes__(
            self
    ) -> bool:
        """
        Read bytes from sensor.

        :return: True if bytes were read and False if the read timed out.
        """

        # output a high-low-high sequence to the component
        gpio.setup(self.pin, gpio.OUT)
        gpio.output(self.pin, gpio.HIGH)
        time.sleep(0.5)
        gpio.output(self.pin, gpio.LOW)
        time.sleep(Hygrothermograph.WAKEUP_SECS)
        gpio.output(self.pin, gpio.HIGH)

        # wait for a low-high-low sequence input sequence
        gpio.setup(self.pin, gpio.IN)
        for value in [gpio.LOW, gpio.HIGH, gpio.LOW]:
            if not self.wait_for(value):
                return False

        # read each byte bit-by-bit
        self.bytes = [0, 0, 0, 0, 0]
        bit_mask = 0x80  # 10000000
        byte_idx = 0
        for _ in range(0, 8 * len(self.bytes)):

            # the chip communicates a 1 or 0 back to us by means of staying high for a long (1) or short (0) interval of
            # time. wait for the high signal.
            if not self.wait_for(gpio.HIGH):
                return False

            # now, time how long it stays high.
            high_start = time.time()
            if not self.wait_for(gpio.LOW):
                return False

            # if the time spent high exceeds the threshold, then record a 1 in the current bit location.
            if time.time() - high_start > self.BIT_HIGH_TIME_THRESHOLD_SECS:
                self.bytes[byte_idx] |= bit_mask

            # shift mask to next bit or reset it to first bit if we're moving to the next byte
            bit_mask >>= 1
            if bit_mask == 0:
                bit_mask = 0x80
                byte_idx += 1

        gpio.setup(self.pin, gpio.OUT)
        gpio.output(self.pin, gpio.HIGH)

        return True

    def wait_for(
            self,
            value: int
    ) -> bool:
        """
        Wait for a GPIO value on the SDA pin.

        :param value: Value to wait for.
        :return: True if value was received within the timeout limit and False if the wait timed out.
        """

        t = time.time()
        while time.time() - t < self.TIMEOUT_SECS:
            if gpio.input(self.pin) == value:
                break
        else:
            return False

        return True


class InfraredMotionSensor(Component):
    """
    Infrared motion sensor (HC SR501).
    """

    class State(Component.State):
        """
        State of sensor.
        """

        def __init__(
                self,
                motion_detected: bool
        ):
            """
            Initialize the state.

            :param motion_detected: Motion is detected.
            """

            self.motion_detected = motion_detected

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, InfraredMotionSensor.State):
                raise ValueError(f'Expected a {InfraredMotionSensor.State}')

            return self.motion_detected == other.motion_detected

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Motion detected:  {self.motion_detected}'

    def __init__(
            self,
            sensor_pin: int
    ):
        """
        Initialize the sensor.

        :param sensor_pin: Sensor pin.
        """

        super().__init__(InfraredMotionSensor.State(False))

        self.sensor_pin = sensor_pin

        gpio.setup(sensor_pin, gpio.IN)
        gpio.add_event_detect(
            self.sensor_pin,
            gpio.BOTH,
            callback=lambda channel: self.set_state(
                InfraredMotionSensor.State(gpio.input(self.sensor_pin) == gpio.HIGH)
            ),
            bouncetime=10
        )


class UltrasonicRangeFinder(Component):
    """
    Ultrasonic range finder (HC SR04).
    """

    SPEED_OF_SOUND_METERS_PER_SECOND = 340.0
    TRIGGER_TIME_SECONDS = 10.0 * 1e-6
    ECHO_TIMEOUT_SECONDS = 0.01

    class State(Component.State):
        """
        State of sensor.
        """

        def __init__(
                self,
                distance_cm: Optional[float]
        ):
            """
            Initialize the state.

            :param distance_cm: Distance from surface (cm).
            """

            self.distance_cm = distance_cm

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, UltrasonicRangeFinder.State):
                raise ValueError(f'Expected a {UltrasonicRangeFinder.State}')

            return self.distance_cm == other.distance_cm

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return 'Distance:  ' + 'None' if self.distance_cm is None else f'{self.distance_cm:.2f} cm'

    def measure_distance_once(
            self
    ) -> Optional[float]:
        """
        Measure distance to surface.

        :return: Distance (cm), or None if distance was unavailable or invalid.
        """

        # signal the sensor to take a measurement
        gpio.output(self.trigger_pin, gpio.HIGH)
        time.sleep(UltrasonicRangeFinder.TRIGGER_TIME_SECONDS)
        gpio.output(self.trigger_pin, gpio.LOW)

        # wait for the echo pin to flip to high
        wait_start_time = time.time()
        while time.time() - wait_start_time < UltrasonicRangeFinder.ECHO_TIMEOUT_SECONDS:
            if gpio.input(self.echo_pin) == gpio.HIGH:
                echo_start_time = time.time()
                break
        else:
            self.set_state(UltrasonicRangeFinder.State(distance_cm=None))
            return None

        # mark the time and wait for the echo pin to flip to low
        while time.time() - echo_start_time < UltrasonicRangeFinder.ECHO_TIMEOUT_SECONDS:
            if gpio.input(self.echo_pin) == gpio.LOW:
                echo_end_time = time.time()
                break
        else:
            self.set_state(UltrasonicRangeFinder.State(distance_cm=None))
            return None

        # measure the time that the echo pin was high and calculate distance accordingly
        echo_time_seconds = echo_end_time - echo_start_time
        total_distance_m = UltrasonicRangeFinder.SPEED_OF_SOUND_METERS_PER_SECOND * echo_time_seconds
        surface_distance_cm = total_distance_m * 100.0 / 2.0
        self.set_state(UltrasonicRangeFinder.State(distance_cm=surface_distance_cm))

        return surface_distance_cm

    def __measure_distance_repeatedly__(
            self
    ):
        """
        Measure distance repeatedly and update state accordingly. This will continue to measure until
        `continue_measuring_distance` becomes False. This is not intended to be called directly; instead, call
        `start_measuring_distance` and `stop_measuring_distance`.
        """

        while self.continue_measuring_distance:
            self.measure_distance_once()
            time.sleep(self.measure_sleep_seconds)

    def start_measuring_distance(
            self
    ):
        """
        Start measuring distance.
        """

        self.stop_measuring_distance()
        self.continue_measuring_distance = True
        self.measure_distance_repeatedly_thread.start()

    def stop_measuring_distance(
            self
    ):
        """
        Stop measuring distance.
        """

        if self.measure_distance_repeatedly_thread.is_alive():
            self.continue_measuring_distance = False
            self.measure_distance_repeatedly_thread.join()

    def __init__(
            self,
            trigger_pin: int,
            echo_pin: int,
            measurements_per_second: float
    ):
        """
        Initialize the sensor.

        :param trigger_pin: Trigger pin.
        :param echo_pin: Echo pin.
        :param measurements_per_second: Measurements per second.
        """

        super().__init__(UltrasonicRangeFinder.State(None))

        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.measurements_per_second = measurements_per_second

        self.measure_sleep_seconds = 1.0 / self.measurements_per_second
        self.continue_measuring_distance = True
        self.measure_distance_repeatedly_thread = Thread(target=self.__measure_distance_repeatedly__)

        gpio.setup(trigger_pin, gpio.OUT, initial=gpio.LOW)
        gpio.setup(self.echo_pin, gpio.IN)


class Camera(Component):
    """
    Camera.
    """

    class DetectedFace:
        """
        Detected face.
        """

        def __init__(
                self,
                center_x: float,
                center_y: float,
                top_left_corner_x: float,
                top_left_corner_y: float,
                width: float,
                height: float
        ):
            """
            Initialize face.

            :param center_x: Center x.
            :param center_y: Center y.
            :param top_left_corner_x: Top-left corner x.
            :param top_left_corner_y: Top-left corner y.
            :param width: Width.
            :param height: Height.
            """

            self.center_x = center_x
            self.center_y = center_y
            self.top_left_corner_x = top_left_corner_x
            self.top_left_corner_y = top_left_corner_y
            self.width = width
            self.height = height

    class State(Component.State):
        """
        Camera state.
        """

        def __init__(
                self
        ):
            """
            Not used.
            """

        def __eq__(self, other: object) -> bool:
            """
            Not used.
            """

            return False

        def __str__(self) -> str:
            """
            Not used.
            """

            return ''

    def multiply_resolution(
            self,
            factor: int
    ):
        """
        Multiply the frame width.

        :param factor: Factor by which to multiply the frame width.
        """

        with self.camera_lock:
            width = self.width * factor
            height = int(width * self.height_width_ratio)
            self.camera.release()
            self.camera = cv2.VideoCapture(self.device, cv2.CAP_V4L)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def get_frame_resolution(
            self
    ) -> Tuple[float, float]:
        """
        Get current frame resolution.

        :return: 2-tuple of width/height.
        """

        return self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def turn_on(
            self
    ):
        """
        Turn the camera on.
        """

        with self.camera_lock:
            self.on = True

    def turn_off(
            self
    ):
        """
        Turn the camera off.
        """

        with self.camera_lock:
            self.on = False

    def capture_image(
            self
    ) -> str:
        """
        Capture image.

        :return: Base-64 encoded string of the byte content of the image.
        """

        with self.camera_lock:
            if self.on:
                image_bytes = self.camera.read()[1]
            else:
                return ''

        if self.run_face_detection:
            detected_faces = self.detect_faces(image_bytes)
            if self.circle_detected_faces:
                image_bytes = self.circle_faces(image_bytes, detected_faces)

        # encode as jpg -> base64 string, and strip the leading b' and trailing '
        image_jpg_bytes = cv2.imencode('.jpg', image_bytes)[1]
        base_64_string_jpg = str(base64.b64encode(image_jpg_bytes))[2:-1]

        return base_64_string_jpg

    def enable_face_detection(
            self
    ):
        """
        Enable face detection.
        """

        self.run_face_detection = True

    def disable_face_detection(
            self
    ):
        """
        Disable face detection.
        """

        self.run_face_detection = False

    def enable_face_circles(
            self
    ):
        """
        Enable face circles.
        """

        self.circle_detected_faces = True

    def disable_face_circles(
            self
    ):
        """
        Disable face circles.
        """

        self.circle_detected_faces = False

    def detect_faces(
            self,
            image_bytes: np.ndarray
    ) -> List[DetectedFace]:
        """
        Detect faces within an image.
        
        :param image_bytes: Image bytes within which to detect faces.
        :return: List of detected faces.
        """

        image_bytes_grayscale = cv2.cvtColor(image_bytes, cv2.COLOR_BGR2GRAY)

        detected_faces = [
            Camera.DetectedFace(
                center_x=float(x + w / 2.0),
                center_y=float(y + h / 2.0),
                top_left_corner_x=x,
                top_left_corner_y=y,
                width=w,
                height=h
            )
            for x, y, w, h in self.face_model.detectMultiScale(image_bytes_grayscale, 1.3, 5)
        ]

        if self.face_detection_callback is not None and len(detected_faces) > 0:
            self.face_detection_callback(detected_faces)

        return detected_faces

    @staticmethod
    def circle_faces(
            image_bytes: np.ndarray,
            detected_faces: List[DetectedFace]
    ) -> np.ndarray:
        """
        Circle detected faces within an image.

        :param image_bytes: Image within which to circle faces.
        :param detected_faces: List of detected faces.
        :return: Image bytes with circles overlaid on faces.
        """

        if len(detected_faces) > 0:
            for detected_face in detected_faces:
                image_bytes = cv2.circle(
                    image_bytes,
                    (int(detected_face.center_x), int(detected_face.center_y)),
                    int((detected_face.width + detected_face.height) / 4),
                    (0, 255, 0),
                    2
                )

        return image_bytes

    def __init__(
            self,
            device: str,
            width: int,
            height: int,
            fps: int,
            run_face_detection: bool,
            circle_detected_faces: bool,
            face_detection_callback: Optional[Callable[[List[DetectedFace]], None]]
    ):
        """
        Initialize camera.

        :param device: Device (e.g., '/dev/video0').
        :param width: Width.
        :param height: Height.
        :param fps: Frames per second.
        :param run_face_detection: Whether to detect faces in captured images.
        :param circle_detected_faces: Whether to circle detected faces in captured images.
        :param face_detection_callback: Callback for face detections.
        """

        super().__init__(Camera.State())

        self.height_width_ratio = 0.75
        if height / width != self.height_width_ratio:
            width = height / self.height_width_ratio

        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.run_face_detection = run_face_detection
        self.circle_detected_faces = circle_detected_faces
        self.face_detection_callback = face_detection_callback

        self.camera = cv2.VideoCapture(self.device, cv2.CAP_V4L)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera_lock = Lock()

        self.face_model = cv2.CascadeClassifier(f'{os.path.dirname(__file__)}/haarcascade_frontalface_default.xml')

        self.on = False


class MjpgStreamer(Component):
    """
    A wrapper around the mjpg-streamer application found here:  https://github.com/jacksonliam/mjpg-streamer
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                on: bool
        ):
            """
            Initialize the state.

            :param on: Whether the streamer is is.
            """

            self.on = on

        def __eq__(self, other: object) -> bool:
            """
            Check equality.

            :param other: Other.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, MjpgStreamer.State):
                raise ValueError(f'Expected a {MjpgStreamer.State}')

            return self.on == other.on

        def __str__(self) -> str:
            """
            Get string.

            :return: String.
            """

            return f'{self.on}'

    def turn_on(
            self
    ):
        """
        Start the stream.
        """

        self.set_state(MjpgStreamer.State(on=True))

    def turn_off(
            self
    ):
        """
        Stop the stream.
        """

        self.set_state(MjpgStreamer.State(on=False))

    def set_state(
            self,
            state: 'Component.State'
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        state: MjpgStreamer.State
        self.state: MjpgStreamer.State

        if state.on and not self.state.on:
            args = shlex.split(f'./mjpg_streamer -i "input_uvc.so -d {self.device} -fps {self.fps} -r {self.width}x{self.height} -q {self.quality}" -o "output_http.so -p {self.port} -w ./www"')
            self.process = subprocess.Popen(args, cwd=os.getenv('MJPG_STREAMER_HOME'))
        elif not state.on and self.state.on:
            os.kill(self.process.pid, signal.SIGTERM)
            while self.process.poll() is None:
                time.sleep(1)

            self.process = None

        super().set_state(state)

    def __init__(
            self,
            device: str,
            width: int,
            height: int,
            fps: int,
            quality: int,
            port: int
    ):
        """
        Initialize the stream.

        :param device: Device (e.g., '/dev/video0').
        :param width: Width.
        :param height: Height.
        :param fps: Frames per second.
        :param quality: Quality (0-100).
        :param port: Port to serve stream on.
        """

        super().__init__(MjpgStreamer.State(on=False))

        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.quality = quality
        self.port = port

        self.process = None


class Tachometer(Component):
    """
    Tachometer driven by signals (e.g., GPIO high/low) indicating the rotational speed of a motor's output.
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                rotations_per_second: float
        ):
            """
            Initialize the state.

            :param rotations_per_second: Rotations per second.
            """

            self.rotations_per_second = rotations_per_second

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Tachometer.State):
                raise ValueError(f'Expected a {Tachometer.State}')

            return self.rotations_per_second == other.rotations_per_second

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'RPS:  {self.rotations_per_second}'

    def record_low_reading(
            self
    ):
        """
        Record a low reading in the tachometer.
        """

        self.state: Tachometer.State

        current_timestamp = time.time()

        if self.previous_rotation_timestamp is None:
            self.previous_rotation_timestamp = current_timestamp

        self.reading_low_count = self.reading_low_count + 1
        if self.reading_low_count % self.low_readings_per_rotation == 0:

            rotations_per_second = 1.0 / (current_timestamp - self.previous_rotation_timestamp)

            if np.isnan(self.state.rotations_per_second):
                smoothed_rotations_per_second = (1.0 - self.smoothing_factor) * rotations_per_second
            else:
                smoothed_rotations_per_second = (
                    self.smoothing_factor * self.state.rotations_per_second +
                    (1.0 - self.smoothing_factor) * rotations_per_second
                )

            self.previous_rotation_timestamp = current_timestamp
            self.set_state(Tachometer.State(smoothed_rotations_per_second))

    def get_rps(
            self
    ) -> float:
        """
        Get current rotations per second (RPS) estimate.

        :return: RPS.
        """

        self.state: Tachometer.State

        return self.state.rotations_per_second

    def __init__(
            self,
            reading_pin: CkPin,
            bounce_time_ms: int,
            read_delay_ms: float,
            low_readings_per_rotation: int,
            smoothing_factor: float
    ):
        """
        Initialize the tachometer.

        :param reading_pin: Reading pin.
        :param bounce_time_ms: Debounce interval (milliseconds). Minimum time between event callbacks.
        :param read_delay_ms: Delay (milliseconds) between event callback and reading the GPIO value of the switch.
        :param low_readings_per_rotation: Number of low readings per rotation.
        :param smoothing_factor: Smoothing factor [0.0, 1.0) to apply to estimated rotations per second. The larger the
        value, the smoother the estimates will be, the larger the bias, the smaller the variance, etc. The smaller the
        value, the rougher the estimates will be, the smaller the bias, the larger the variance, etc.
        """

        super().__init__(Tachometer.State(np.nan))

        self.reading_pin = reading_pin
        self.bounce_time_ms = bounce_time_ms
        self.read_delay_ms = read_delay_ms
        self.low_readings_per_rotation = low_readings_per_rotation
        self.smoothing_factor = smoothing_factor

        self.previous_rotation_timestamp: Optional[float] = None
        self.reading_low_count = 0
        self.reading_pseudo_button = TwoPoleButton(
            input_pin=reading_pin,
            bounce_time_ms=self.bounce_time_ms,
            read_delay_ms=self.read_delay_ms
        )
        self.reading_pseudo_button.event(lambda s: self.record_low_reading() if s.pressed else None)


class RotaryEncoder(Component):
    """
    Rotary encoder designed with a 2-phase rectangular orthogonal circuit. See, for example, the item listed at the
    following URL:

      https://www.amazon.com/dp/B00UTIFCVA

    Note that, as of 12 December 2023, the wiring instructions listed in the item description are incorrect. Here are
    the correct wiring instructions:

      * Red wire:  5v input power
      * Black wire:  Ground
      * White wire:  Phase-a signal
      * Green wire:  Phase-b signal

    Be careful when wiring the rotary encoder, as incorrectly supplying power through the phase signals can damage the
    encoder's internal circuitry.
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                degrees: float,
                degrees_per_second: float,
                clockwise: bool
        ):
            """
            Initialize the state.

            :param degrees: Degrees of rotation.
            :param degrees_per_second: Degrees per second.
            :param clockwise: Whether the encoder is turning in a clockwise direction.
            """

            self.degrees = degrees
            self.degrees_per_second = degrees_per_second
            self.clockwise = clockwise

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, RotaryEncoder.State):
                raise ValueError(f'Expected a {RotaryEncoder.State}')

            return (
                self.degrees == other.degrees and
                self.degrees_per_second == other.degrees_per_second and
                self.clockwise == other.clockwise
            )

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'{self.degrees:.1f} deg @ {self.degrees_per_second:.1f} deg/s clockwise={self.clockwise}'

    def phase_a_changed(
            self,
            up: bool
    ):
        """
        Record phase-a changed.

        :param up: Whether phase-a is up (True) or down (False).
        """

        previous_time_epoch = self.current_time_epoch
        self.current_time_epoch = time.time()
        self.phase_a_reporting = True
        self.phase_a_high = up

        if self.phase_a_high == self.phase_b_high:
            self.phase_change_index += 1
        else:
            self.phase_change_index -= 1

        self.phase_changes += 1

        if self.phase_a_reporting and self.phase_b_reporting:
            previous_degrees = self.degrees
            self.degrees = (self.phase_change_index / self.phase_changes_per_degree) % 360.0
            self.degrees_per_second = (
                abs(self.degrees - previous_degrees) /
                (self.current_time_epoch - previous_time_epoch)
            )
            self.clockwise = self.degrees > previous_degrees
            if self.report_state:
                self.set_state(RotaryEncoder.State(self.degrees, self.degrees_per_second, self.clockwise))

    def phase_b_changed(
            self,
            up: bool
    ):
        """
        Record phase-b changed.

        :param up: Whether phase-b is up (True) or down (False).
        """

        previous_time_epoch = self.current_time_epoch
        self.current_time_epoch = time.time()
        self.phase_b_reporting = True
        self.phase_b_high = up

        if self.phase_b_high == self.phase_a_high:
            self.phase_change_index -= 1
        else:
            self.phase_change_index += 1

        self.phase_changes += 1

        if self.phase_a_reporting and self.phase_b_reporting:
            previous_degrees = self.degrees
            self.degrees = (self.phase_change_index / self.phase_changes_per_degree) % 360.0
            self.degrees_per_second = (
                abs(self.degrees - previous_degrees) /
                (self.current_time_epoch - previous_time_epoch)
            )
            self.clockwise = self.degrees > previous_degrees
            if self.report_state:
                self.set_state(RotaryEncoder.State(self.degrees, self.degrees_per_second, self.clockwise))

    def __init__(
            self,
            phase_a_pin: CkPin,
            phase_b_pin: CkPin,
            phase_changes_per_rotation: int,
            report_state: bool
    ):
        """
        Initialize the rotary encoder.

        :param phase_a_pin: Phase-a pin.
        :param phase_b_pin: Phase-b pin.
        :param phase_changes_per_rotation: Number of phase changes per rotation.
        :param report_state: Whether to report state when rotation changes. Because rotary encoders usually need to have
        very low latency, the added overhead of reporting state can be too much. Pass True here to report state update
        events in the usual way (more overhead and higher latency), or pass False here to not report state update events
        (less overhead and lower latency).
        """

        super().__init__(RotaryEncoder.State(0.0, 0.0, False))

        self.phase_a_pin = phase_a_pin
        self.phase_b_pin = phase_b_pin
        self.phase_changes_per_rotation = phase_changes_per_rotation
        self.report_state = report_state

        self.phase_changes_per_degree = self.phase_changes_per_rotation / 360.0
        self.phase_change_index = 0
        self.phase_changes = 0
        self.degrees = 0.0
        self.degrees_per_second = 0.0
        self.clockwise = False
        self.phase_a_high = False
        self.phase_a_reporting = False
        self.phase_b_high = False
        self.phase_b_reporting = False
        self.current_time_epoch = None

        gpio.setup(self.phase_a_pin, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.add_event_detect(
            self.phase_a_pin,
            gpio.BOTH,
            callback=lambda channel: self.phase_a_changed(gpio.input(self.phase_a_pin) == gpio.LOW)
        )

        gpio.setup(self.phase_b_pin, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.add_event_detect(
            self.phase_b_pin,
            gpio.BOTH,
            callback=lambda channel: self.phase_b_changed(gpio.input(self.phase_b_pin) == gpio.LOW)
        )
