from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict

from smbus2 import SMBus

from raspberry_py.gpio import Component


class AdcDevice(Component, ABC):
    """
    Abstract analog-to-digital converter.
    """

    class State(Component.State):
        """
        ADC state.
        """

        def __init__(
                self,
                channel_value: Optional[Dict[int, float]]
        ):
            """
            Initialize the state.

            :param channel_value: Channels and values.
            """

            self.channel_value = channel_value

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, AdcDevice.State):
                raise ValueError(f'Expected a {AdcDevice.State}')

            return self.channel_value == other.channel_value

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return str(self.channel_value)

    @abstractmethod
    def analog_read(
            self,
            channel: int
    ) -> int:
        """
        Read a byte.

        :param channel: Channel.
        :return: Digital value.
        """

    def update_state(
            self
    ):
        """
        Update state.
        """

        channel_value = {}

        for channel in self.channel_rescaled_range:

            digital_value = self.analog_read(channel)
            if not self.digital_range[0] <= digital_value <= self.digital_range[1]:
                raise ValueError('Out of range.')

            # get rescaled range and check for reversed range
            rescaled_range = self.channel_rescaled_range[channel]
            reversed_range = rescaled_range is not None and rescaled_range[0] > rescaled_range[1]
            if reversed_range:
                rescaled_range = sorted(rescaled_range)

            # rescale if a range is provided for the channel
            if rescaled_range is not None:

                digital_range_total = self.digital_range[1] - self.digital_range[0]
                digital_range_fraction = (digital_value - self.digital_range[0]) / digital_range_total
                if reversed_range:
                    digital_range_fraction = 1.0 - digital_range_fraction

                rescaled_range_total = rescaled_range[1] - rescaled_range[0]
                digital_value = rescaled_range[0] + digital_range_fraction * rescaled_range_total

            channel_value[channel] = digital_value

        self.set_state(AdcDevice.State(channel_value=channel_value))

    def invert_digital_value(
            self,
            value: float,
            channel: int
    ) -> float:
        """
        Invert a digital value within its range. If the given value is 23% of its range, then the inverted value will be
        77% of its range (and vice-versa). The range used will either be the native range of the A/D converter, or it
        will be the rescaled range if one was provided for the channel to __init__.

        :param value: Value.
        :param channel: Channel.
        :return: Inverted value.
        """

        value_range = self.channel_rescaled_range[channel]
        if value_range is None:
            value_range = self.digital_range

        range_min, range_max = value_range
        if range_min > range_max:
            raise ValueError('It does not make much sense to invert a reversed range.')

        range_total = range_max - range_min
        range_fraction = 1.0 - (value - range_min) / range_total

        return range_min + range_fraction * range_total

    def get_voltage(
            self,
            digital_output: int
    ) -> float:
        """
        Get analog voltage corresponding to a digital output.

        :param digital_output: Digital output.
        :return: Approximate voltage.
        """

        return self.input_voltage * (digital_output / self.digital_range[1])

    def get_channel_value(
            self
    ) -> Dict[int, float]:
        """
        Get channel-value dictionary from current state.

        :return: Channel-value dictionary.
        """

        state: AdcDevice.State = self.get_state()

        return state.channel_value

    def __init__(
            self,
            input_voltage: float,
            bus: SMBus,
            address: int,
            command: int,
            digital_range: Tuple[int, int],
            channel_rescaled_range: Dict[int, Optional[Tuple[float, float]]]
    ):
        """
        Initialize the ADC.

        :param input_voltage: Input voltage (typically 3.3).
        :param bus: Bus.
        :param address: Address.
        :param command: Command.        
        :param digital_range: Native range of ADC.
        :param channel_rescaled_range: Channels to use and their rescaled output ranges. Pass None for the ranges to use
        the native digital range of the ADC device.
        """

        super().__init__(
            state=AdcDevice.State(None)
        )

        self.input_voltage = input_voltage
        self.bus = bus
        self.cmd = command
        self.address = address
        self.digital_range = digital_range
        self.channel_rescaled_range = channel_rescaled_range

    def close(self):
        """
        Close the device.
        """

        self.bus.close()


class PCF8591(AdcDevice):
    """
    PCF8591 ADC.
    """

    # default address. check the address with `i2cdetect -y 1`.
    ADDRESS = 0x48

    # default command.
    COMMAND = 0x40

    def __init__(
            self,
            input_voltage: float,
            bus: SMBus,
            address: int,
            command: int,
            channel_rescaled_range: Dict[int, Optional[Tuple[float, float]]]
    ):
        """
        Initialize the PCF8591.

        :param input_voltage: Input voltage (typically 3.3).
        :param bus: Bus.
        :param address: Address.
        :param command: Command.        
        :param channel_rescaled_range: Channels to use and their rescaled output ranges. Pass None for the ranges to use
        the native digital range of the ADC device.
        """

        super().__init__(
            input_voltage=input_voltage,
            bus=bus,
            address=address,
            command=command,
            digital_range=(0, 255),
            channel_rescaled_range=channel_rescaled_range
        )

    def analog_read(
            self,
            channel: int
    ) -> int:
        """
        Read a byte.

        :param channel: The PCF8591 has 4 ADC input pins:  0, 1, 2, and 3.
        :return: Digital value.
        """

        return self.bus.read_byte_data(self.address, self.cmd + channel)

    def analog_write(
            self,
            address: int,
            cmd: int,
            value: int
    ):
        """
        Write a byte.

        :param address: Address.
        :param cmd: Command.
        :param value: Value.
        """

        self.bus.write_byte_data(address, cmd, value)


class ADS7830(AdcDevice):
    """
    ADS7830 ADC. See the docs/ads7830.pdf datasheet for full information.
    """

    # default address:  bin(0x4b) == 1001011. check the address with `i2cdetect -y 1`.
    ADDRESS = 0x4b

    # default command (single-ended inputs, internal reference off, A/D on):  bin(0x84) == 10000100. see page 13 of the
    # datasheet for the layout of this byte.
    COMMAND = 0x84

    def __init__(
            self,
            input_voltage: float,
            bus: SMBus,
            address: int,
            command: int,
            channel_rescaled_range: Dict[int, Optional[Tuple[float, float]]]
    ):
        """
        Initialize the ADS7830.

        :param input_voltage: Input voltage (typically 3.3).
        :param bus: Bus.
        :param address: Address.
        :param command: Command.        
        :param channel_rescaled_range: Channels to use and their rescaled output ranges. Pass None for the ranges to use
        the native digital range of the ADC device.
        """

        super().__init__(
            input_voltage=input_voltage,
            bus=bus,
            command=command,
            address=address,
            digital_range=(0, 255),
            channel_rescaled_range=channel_rescaled_range
        )

    def analog_read(
            self,
            channel: int
    ) -> int:
        """
        Read a byte.

        :param channel: The ADS7830 has 8 ADC input pins:  0, 1, 2, 3, 4, 5, 6, and 7.
        :return: Digital value.
        """

        # see page 14 of the datasheet for channel selection control. there are 8 channels and thus 3 channel selection
        # bits. the MSB of the channel selection bits indicates whether an even or odd channel is selected, and the
        # final two bits indicate which of the even (or odd) channels is selected. then we shift the resulting 3 bits
        # over 4 places to put them into correct position within the byte (see page 13).
        return self.bus.read_byte_data(self.address, self.cmd | (((channel << 2 | channel >> 1) & 0x07) << 4))
