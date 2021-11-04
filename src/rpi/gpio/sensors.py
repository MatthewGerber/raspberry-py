import math


class Thermistor:
    """
    Thermistor, to be connected via ADC.
    """

    @staticmethod
    def get_temperature(
            voltage: float,
            input_voltage: float
    ) -> float:
        """
        Get temperature from voltage.

        :param voltage: Voltage.
        :param input_voltage: Input voltage.
        :return: Temperature (F).
        """

        Rt = 10.0 * voltage / (input_voltage - voltage)
        temp_k = 1 / (1 / (273.15 + 25) + math.log(Rt / 10.0) / 3950.0)
        temp_c = temp_k - 273.15
        temp_f = temp_c * (9.0 / 5.0) + 32.0

        return temp_f
