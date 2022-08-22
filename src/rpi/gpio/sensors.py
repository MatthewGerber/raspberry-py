import math
import time
from enum import Enum, auto
from typing import Optional

import datetime
import RPi.GPIO as gpio

from rpi.gpio import Component
from rpi.gpio.adc import AdcDevice


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

            return f'Distance:  {self.distance_cm}'

    def measure_distance(
            self
    ):
        """
        Measure distance to surface.
        """

        gpio.output(self.trigger_pin, gpio.HIGH)
        time.sleep(10.0 * 1e-6)
        gpio.output(self.trigger_pin, gpio.LOW)

    def echo_pin_changed(
            self,
            high: bool
    ):
        if high:
            self.trigger_time = datetime.datetime.now()
        elif self.trigger_time is not None:
            echo_time = datetime.datetime.now() - self.trigger_time
            distance_cm = (340.0 * echo_time.total_seconds()) * 1000.0
            self.set_state(UltrasonicRangeFinder.State(distance_cm=distance_cm))
            self.trigger_time = None

    def __init__(
            self,
            trigger_pin: int,
            echo_pin: int
    ):
        """
        Initialize the sensor.

        :param trigger_pin: Trigger pin.
        :param echo_pin: Echo pin.
        """

        super().__init__(UltrasonicRangeFinder.State(None))

        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin

        self.trigger_time = None

        gpio.setup(trigger_pin, gpio.OUT, initial=gpio.LOW)
        gpio.setup(self.echo_pin, gpio.IN)
        gpio.add_event_detect(
            self.echo_pin,
            gpio.BOTH,
            callback=lambda channel: self.echo_pin_changed(gpio.input(self.echo_pin) == gpio.HIGH),
            bounce_time_ms=0
        )
