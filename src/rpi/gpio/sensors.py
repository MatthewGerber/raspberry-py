import math
from typing import Optional

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
            voltage: float,
            input_voltage: float
    ) -> float:
        """
        Convert temperature to voltage.

        :param voltage: Voltage.
        :param input_voltage: Input voltage.
        :return: Temperature (F).
        """

        rt = 10.0 * voltage / (input_voltage - voltage)
        temp_k = 1 / (1 / (273.15 + 25) + math.log(rt / 10.0) / 3950.0)
        temp_c = temp_k - 273.15
        temp_f = temp_c * (9.0 / 5.0) + 32.0

        return temp_f

    def get_temperature_f(
            self
    ) -> float:
        """
        Get temperature (F).

        :return: Temperature (F).
        """

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
        :param channel: Analog-to-digital channel on which to monitor values.
        """

        super().__init__(Thermistor.State(temperature_f=None))

        self.adc = adc
        self.channel = channel

        self.adc.event(
            lambda s: self.set_state(
                Thermistor.State(
                    temperature_f=self.convert_voltage_to_temperature(
                        voltage=adc.get_voltage(
                            digital_output=s.channel_value[self.channel]
                        ),
                        input_voltage=self.adc.input_voltage
                    )
                )
            )
        )
