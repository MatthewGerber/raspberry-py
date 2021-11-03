from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict

from smbus2 import SMBus

from rpi.gpio import Component


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
                channel_value: Optional[Dict[int, int]]
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
        Read a value.

        :param channel: Channel.
        :return: Value.
        """

    def update_state(
            self
    ):
        """
        Update state.
        """

        channel_value = {}

        for channel in self.channel_rescaled_range:

            # read native value and ensure that it is in range
            value = self.analog_read(channel)
            if not self.digital_range[0] <= value <= self.digital_range[1]:
                raise ValueError('Out of range.')

            # rescale if a range is provided for the channel
            rescaled_range = self.channel_rescaled_range[channel]
            if rescaled_range is not None:
                native_range_total = self.digital_range[1] - self.digital_range[0]
                native_range_fraction = (value - self.digital_range[0]) / native_range_total
                rescaled_range_total = rescaled_range[1] - rescaled_range[0]
                value = round(rescaled_range[0] + native_range_fraction * rescaled_range_total)

            channel_value[channel] = value

        self.set_state(AdcDevice.State(channel_value=channel_value))

    def __init__(
            self,
            bus: SMBus,
            cmd: int,
            address: int,
            digital_range: Tuple[int, int],
            channel_rescaled_range: Dict[int, Optional[Tuple[int, int]]]
    ):
        """
        Initialize the ADC.

        :param bus: Bus.
        :param cmd: Command.
        :param address: Address.
        :param digital_range: Native range of ADC.
        :param channel_rescaled_range: Channels to use and their rescaled output ranges. Pass None for the ranges to use
        the native digital range of the ADC device.
        """

        super().__init__(
            state=AdcDevice.State(None)
        )

        self.bus = bus
        self.cmd = cmd
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

    # default command.
    COMMAND = 0x40

    # default address. check the address with `i2cdetect -y 1`.
    ADDRESS = 0x48

    def __init__(
            self,
            bus: SMBus,
            cmd: int,
            address: int,
            channel_rescaled_range: Dict[int, Optional[Tuple[int, int]]]
    ):
        """
        Initialize the PCF8591.

        :param bus: Bus.
        :param cmd: Command.
        :param address: Address.
        :param channel_rescaled_range: Channels to use and their rescaled output ranges. Pass None for the ranges to use
        the native digital range of the ADC device.
        """

        super().__init__(
            bus=bus,
            cmd=cmd,
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

        :param channel: The PCF8591 has 4 ADC input pins:  0, 1, 2, and 3.
        :return: Value.
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
    ADS7830 ADC.
    """

    # default command.
    COMMAND = 0x84

    # default address. check the address with `i2cdetect -y 1`.
    ADDRESS = 0x4b

    def __init__(
            self,
            bus: SMBus,
            cmd: int,
            address: int,
            channel_rescaled_range: Dict[int, Optional[Tuple[int, int]]]
    ):
        """
        Initialize the ADS7830.

        :param bus: Bus.
        :param cmd: Command.
        :param address: Address.
        :param channel_rescaled_range: Channels to use and their rescaled output ranges. Pass None for the ranges to use
        the native digital range of the ADC device.
        """

        super().__init__(
            bus=bus,
            cmd=cmd,
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
        :return: Value.
        """

        return self.bus.read_byte_data(self.address, self.cmd | (((channel << 2 | channel >> 1) & 0x07) << 4))
