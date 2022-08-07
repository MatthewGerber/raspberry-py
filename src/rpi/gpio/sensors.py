import math
import time
from enum import Enum, auto
from typing import Optional

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
    BYTE_HIGH_TIME_THRESHOLD_SECS = 0.00005

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
                humidity = self.bytes[0]
                temperature_c = (self.bytes[2] + self.bytes[3] * 0.1)
                temperature_f = temperature_c * 9.0/5.0 + 32.0
                checksum = (self.bytes[0] + self.bytes[1] + self.bytes[2] + self.bytes[3]) & 0xFF
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

        # clear sda
        gpio.setup(self.pin, gpio.OUT)
        gpio.output(self.pin, gpio.HIGH)
        time.sleep(0.5)

        # start signal
        gpio.output(self.pin, gpio.LOW)
        time.sleep(Hygrothermograph.WAKEUP_SECS)
        gpio.output(self.pin, gpio.HIGH)
        gpio.setup(self.pin, gpio.IN)

        # wait for a low-high-low sequence
        for value in [gpio.LOW, gpio.HIGH, gpio.LOW]:
            if not self.wait_for(value):
                return False

        # read each byte bit-by-bit
        self.bytes = [0, 0, 0, 0, 0]
        mask = 0x80
        byte_idx = 0
        for _ in range(0, 8 * len(self.bytes)):

            if not self.wait_for(gpio.HIGH):
                return False

            t = time.time()

            if not self.wait_for(gpio.LOW):
                return False

            if time.time() - t > self.BYTE_HIGH_TIME_THRESHOLD_SECS:
                self.bytes[byte_idx] |= mask

            mask >>= 1
            if mask == 0:
                mask = 0x80
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
