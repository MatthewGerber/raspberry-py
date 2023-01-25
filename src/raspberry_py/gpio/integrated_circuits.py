import math
import time
from typing import Optional, Union, List

import RPi.GPIO as gpio
from smbus2 import SMBus

from raspberry_py.gpio import Component


class ShiftRegister74HC595(Component):
    """
    74HC595:  Serial-to-parallel data shift register.
    """

    class State(Component.State):
        """
        State of register.
        """

        def __init__(
                self,
                enabled: bool,
                x: Optional[Union[int, List[int]]]
        ):
            """
            Initialize the state.

            :param enabled: Whether the register is enabled.
            :param x: Output value, either a single integer (for one shift-register) or a list of integers (for multiple
            shift-registers connected in series). In the latter case, the first list element will be written to the
            first shift-register in the series, the second list element will be written to the second shift-register in
            the series, and so on.
            """

            self.enabled = enabled
            self.x = x

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, ShiftRegister74HC595.State):
                raise ValueError(f'Expected a {ShiftRegister74HC595.State}')

            return self.enabled == other.enabled and self.x == other.x

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Enabled:  {self.enabled}, Value:  {self.x}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, ShiftRegister74HC595.State):
            raise ValueError(f'Expected a {ShiftRegister74HC595.State}')

        state: ShiftRegister74HC595.State

        if self.output_disable_pin is not None:
            gpio.output(self.output_disable_pin, gpio.LOW if state.enabled else gpio.HIGH)

        if state.x is not None:

            # get value(s) to write to a single shift-register (or multiple shift-registers connected in series)
            if isinstance(state.x, int):
                values_to_write = [state.x]
            elif isinstance(state.x, list):
                values_to_write = state.x
            else:
                raise ValueError(f'Unknown value:  {state.x}')

            gpio.output(self.write_register_to_output_pin, gpio.LOW)

            # write all values
            for value_to_write in values_to_write:

                bit_length = value_to_write.bit_length()
                if bit_length > self.bits:
                    raise ValueError(f'Cannot write {bit_length} bits to an 8-bit shift register.')

                # write msb first, flipping the shift register pin each time.
                for bit_idx in reversed(range(self.bits)):
                    bit_value = (value_to_write >> bit_idx) & 1
                    gpio.output(self.shift_register_pin, gpio.LOW)
                    gpio.output(self.serial_data_input_pin, gpio.HIGH if bit_value == 1 else gpio.LOW)
                    gpio.output(self.shift_register_pin, gpio.HIGH)

            # write to parallel output(s)
            gpio.output(self.write_register_to_output_pin, gpio.HIGH)

        super().set_state(state)

    def enable(
            self
    ):
        """
        Enable the shift register.
        """

        self.state: ShiftRegister74HC595.State
        self.set_state(ShiftRegister74HC595.State(True, self.state.x))

    def disable(
            self
    ):
        """
        Disable the shift register.
        """

        self.state: ShiftRegister74HC595.State
        self.set_state(ShiftRegister74HC595.State(False, self.state.x))

    def write(
            self,
            x: Union[int, List[int]]
    ):
        """
        Write one or more values to the shift register(s) and output to parallel.

        :param x: Value(s).
        """

        self.state: ShiftRegister74HC595.State
        self.set_state(ShiftRegister74HC595.State(self.state.enabled, x))

    def clear(
            self
    ):
        """
        Clear the shift register.
        """

        self.state: ShiftRegister74HC595.State
        self.set_state(ShiftRegister74HC595.State(True, 0))

    def __init__(
            self,
            bits: int,
            output_disable_pin: Optional[int],
            serial_data_input_pin: int,
            shift_register_pin: int,
            write_register_to_output_pin: int,
            register_active_pin: Optional[int]
    ):
        """
        Initialize the shift register.

        :param bits: Number of bits in the shift register.
        :param output_disable_pin: Output disable pin. Pass None and wire to ground to keep output enabled always;
        otherwise, if wired to GPIO port, call `enable` before `write`.
        :param serial_data_input_pin: Serial data input pin.
        :param shift_register_pin: Shift register pin.
        :param write_register_to_output_pin: Write to output pin.
        :param register_active_pin: Register activation pin. Pass None and wire to 3.3v to keep register active always.
        """

        super().__init__(ShiftRegister74HC595.State(False, None))

        self.bits = bits
        self.output_disable_pin = output_disable_pin
        self.serial_data_input_pin = serial_data_input_pin
        self.shift_register_pin = shift_register_pin
        self.write_register_to_output_pin = write_register_to_output_pin
        self.register_active_pin = register_active_pin

        if self.output_disable_pin is not None:
            gpio.setup(self.output_disable_pin, gpio.OUT)

        gpio.setup(self.serial_data_input_pin, gpio.OUT)
        gpio.setup(self.shift_register_pin, gpio.OUT)
        gpio.setup(self.write_register_to_output_pin, gpio.OUT)

        if self.register_active_pin is not None:
            gpio.setup(self.register_active_pin, gpio.OUT)
            gpio.output(self.register_active_pin, gpio.HIGH)  # activate the register pin


class PulseWaveModulatorPCA9685PW:
    """
    PCA9685PW:  16-channel pulse-wave modulator.
    """

    PCA9685PW_ADDRESS = 0x40

    # Registers/etc.
    __SUBADR1 = 0x02
    __SUBADR2 = 0x03
    __SUBADR3 = 0x04
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06
    __LED0_ON_H = 0x07
    __LED0_OFF_L = 0x08
    __LED0_OFF_H = 0x09
    __ALLLED_ON_L = 0xFA
    __ALLLED_ON_H = 0xFB
    __ALLLED_OFF_L = 0xFC
    __ALLLED_OFF_H = 0xFD

    def write(
            self,
            register: int,
            value: int
    ):
        """
        Write an 8-bit value to a register.

        :param register: Register to write.
        :param value: Value to write.
        """

        self.bus.write_byte_data(self.address, register, value)

    def read(
            self,
            register: int
    ) -> int:
        """
        Read an unsigned byte from a register.

        :param register: Register to read.
        :return: Value.
        """

        return self.bus.read_byte_data(self.address, register)

    def set_pwm_frequency(
            self,
            frequency_hz: int
    ):
        """
        Set pulse-wave modulation frequency.

        :param frequency_hz: Frequency (Hz).
        """

        prescale_value = 25000000.0  # 25MHz
        prescale_value /= 4096.0  # 12-bit
        prescale_value /= float(frequency_hz)
        prescale_value -= 1.0
        prescale_value = math.floor(prescale_value + 0.5)

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10  # sleep
        self.write(self.__MODE1, newmode)  # go to sleep
        self.write(self.__PRESCALE, int(prescale_value))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def get_tick(
            self,
            offset_ms: float
    ) -> int:
        """
        Get tick for an offset into the PWM period.

        :param offset_ms:  Offset (ms) into the PWM period.
        """

        if offset_ms > self.period_ms:
            raise ValueError(f'Offset {offset_ms} must be <= the period {self.period_ms}')

        if offset_ms < 0.0:
            raise ValueError(f'Offset {offset_ms} be >= 0.0')

        percentage_of_period = offset_ms / self.period_ms

        return int(percentage_of_period * 4095)

    def set_channel_pwm_on_off(
            self,
            channel: int,
            on_tick: int,
            off_tick: int
    ):
        """
        Set the on/off ticks for an output channel.

        :param channel: Output channel (0-15)
        :param on_tick: On tick in [0,4095].
        :param off_tick: Off tick in [0,4095].
        """

        # each output channel (e.g., led) is controlled by 2 12-bit registers. each register is fed by 2 input channels,
        # one for the lower byte and one for the higher byte (the highest 4 bits are unused). thus, there are 4 input
        # channels per output channel. the 2 registers specify, respectively, the on and off times of the output channel
        # from the range [0,4095].
        channel_register_offset = 4 * channel

        # write lower/higher byte of the on time
        self.write(self.__LED0_ON_L + channel_register_offset, on_tick & 0xFF)
        self.write(self.__LED0_ON_H + channel_register_offset, on_tick >> 8)

        # write lower/higher byte of the off time
        self.write(self.__LED0_OFF_L + channel_register_offset, off_tick & 0xFF)
        self.write(self.__LED0_OFF_H + channel_register_offset, off_tick >> 8)

    def __init__(
            self,
            bus: SMBus,
            address: int,
            frequency_hz: int
    ):
        """
        Instantiate the PWM IC.

        :param bus: Bus.
        :param address: I2C address.
        :param frequency_hz: PWM frequency.
        """

        self.bus = bus
        self.address = address
        self.frequency_hz = frequency_hz

        self.period_ms = 1000.0 / self.frequency_hz
        self.write(self.__MODE1, 0x00)
        self.set_pwm_frequency(self.frequency_hz)
