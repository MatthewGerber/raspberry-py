import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple

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
                channel: Optional[int],
                value: Optional[int]
        ):
            """
            Initialize the state.

            :param channel: Channel.
            :param value: Value.
            """

            self.channel = channel
            self.value = value

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

            return self.channel == other.channel and self.value == other.value

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Channel {self.channel}:  {self.value}'

    @staticmethod
    def detect_i2c(
            bus: str,
            digital_range_scale: Optional[Tuple[int, int]]
    ) -> 'AdcDevice':
        """
        Detect an ADC device.

        :param bus: Bus (e.g., /dev/i2c-1).
        :param digital_range_scale: ADC range low and high values, or None to use raw digital values.
        :return: ADC Device.
        """

        sm_bus = SMBus(bus)

        try:
            sm_bus.write_byte(PCF8591.ADDRESS, 0)
            return PCF8591(
                bus=sm_bus,
                cmd=PCF8591.COMMAND,
                address=PCF8591.ADDRESS,
                digital_range_scale=digital_range_scale
            )
        except Exception as e:
            logging.info(f'{e}')

        try:
            sm_bus.write_byte(ADS7830.ADDRESS, 0)
            return ADS7830(
                bus=sm_bus,
                cmd=ADS7830.COMMAND,
                address=ADS7830.ADDRESS,
                digital_range_scale=digital_range_scale
            )
        except Exception as e:
            logging.info(f'{e}')

        raise ValueError('Failed to detect ADC.')

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
            self,
            channel: int
    ):
        """
        Update state of a channel.

        :param channel: Channel.
        """

        value = self.analog_read(channel)

        if not self.digital_range[0] <= value <= self.digital_range[1]:
            raise ValueError('Out of range.')

        if self.digital_range_scale is not None:
            range_frac = (value - self.digital_range[0]) / (self.digital_range[1] - self.digital_range[0])
            scaled_range = self.digital_range_scale[1] + self.digital_range_scale[0]
            value = round(self.digital_range_scale[0] + range_frac * scaled_range)

        self.set_state(
            AdcDevice.State(
                channel=channel,
                value=value
            )
        )

    def __init__(
            self,
            bus: SMBus,
            cmd: int,
            address: int,
            digital_range: Tuple[int, int],
            digital_range_scale: Optional[Tuple[int, int]]
    ):
        """
        Initialize the ADC.

        :param bus: Bus.
        :param cmd: Command.
        :param address: Address.
        :param digital_range: ADC range low and high values, or None to use raw digital values.
        :param digital_range_scale: Scale.
        """

        super().__init__(
            state=AdcDevice.State(None, None)
        )

        self.bus = bus
        self.cmd = cmd
        self.address = address
        self.digital_range = digital_range
        self.digital_range_scale = digital_range_scale

    def close(self):
        """
        Close the device.
        """

        self.bus.close()


class PCF8591(AdcDevice):
    """
    PCF8591 ADC.
    """

    COMMAND = 0x40
    ADDRESS = 0x48

    def __init__(
            self,
            bus: SMBus,
            cmd: int,
            address: int,
            digital_range_scale: Optional[Tuple[int, int]]
    ):
        """
        Initialize the PCF8591.

        :param bus: Bus.
        :param cmd: Command.
        :param address: Address.
        :param digital_range_scale: Scale.
        """

        super().__init__(
            bus=bus,
            cmd=cmd,
            address=address,
            digital_range=(0, 255),
            digital_range_scale=digital_range_scale
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

    COMMAND = 0x84
    ADDRESS = 0x4b

    def __init__(
            self,
            bus: SMBus,
            cmd: int,
            address: int,
            digital_range_scale: Optional[Tuple[int, int]]
    ):
        """
        Initialize the ADS7830.

        :param bus: Bus.
        :param cmd: Command.
        :param address: Address.
        :param digital_range_scale: Scale.
        """

        super().__init__(
            bus=bus,
            cmd=cmd,
            address=address,
            digital_range=(0, 255),
            digital_range_scale=digital_range_scale
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
