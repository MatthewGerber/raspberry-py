from typing import Optional

import RPi.GPIO as gpio

from rpi.gpio import Component


class ShiftRegister(Component):
    """
    Shift register for serial-to-parallel data conversion. Compatible with the 74HC595 IC (see datasheet in docs).
    """

    class State(Component.State):
        """
        State of register.
        """

        def __init__(
                self,
                enabled: bool,
                x: Optional[int]
        ):
            """
            Initialize the state.

            :param enabled: Whether the register is enabled.
            :param x: Output value.
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

            if not isinstance(other, ShiftRegister.State):
                raise ValueError(f'Expected a {ShiftRegister.State}')

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
            state: 'Component.State'
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, ShiftRegister.State):
            raise ValueError(f'Expected a {ShiftRegister.State}')

        state: ShiftRegister.State

        gpio.output(self.output_disable_pin, gpio.LOW if state.enabled else gpio.HIGH)

        # write serial bits to parallel output if we have a value
        if state.x is not None:

            bit_length = state.x.bit_length()
            if bit_length > self.bits:
                raise ValueError(f'Cannot write {bit_length} bits to an 8-bit shift register.')
            
            gpio.output(self.write_register_to_output_pin, gpio.LOW)

            for bit_idx in reversed(range(self.bits)):
                bit_value = (state.x >> bit_idx) & 1
                gpio.output(self.shift_register_pin, gpio.LOW)
                gpio.output(self.serial_data_input_pin, gpio.HIGH if bit_value == 1 else gpio.LOW)
                gpio.output(self.shift_register_pin, gpio.HIGH)

            # write to output
            gpio.output(self.write_register_to_output_pin, gpio.HIGH)

        super().set_state(state)

    def enable(
            self
    ):
        """
        Enable the shift register.
        """

        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(True, self.state.x))

    def disable(
            self
    ):
        """
        Disable the shift register.
        """

        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(False, self.state.x))

    def write(
            self,
            x: int
    ):
        """
        Write a value to the shift register (and output it).

        :param x: Value.
        """

        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(self.state.enabled, x))

    def clear(
            self
    ):
        """
        Clear the shift register.
        """

        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(True, 0))

    def __init__(
            self,
            bits: int,
            output_disable_pin: int,
            serial_data_input_pin: int,
            shift_register_pin: int,
            write_register_to_output_pin: int,
            register_active_pin: int
    ):
        """
        Initialize the shift register.

        :param bits: Number of bits in the shift register.
        :param output_disable_pin: Output disable pin. Can hard-wire to ground to keep output enabled always; otherwise,
        will need to call `enable` before `write`.
        :param serial_data_input_pin: Serial data input pin.
        :param shift_register_pin: Shift register pin.
        :param write_register_to_output_pin: Write to output pin.
        :param register_active_pin: Register activation pin (can hard-wire to 3.3v to keep register active always).
        """

        super().__init__(ShiftRegister.State(False, None))

        self.bits = bits
        self.output_disable_pin = output_disable_pin
        self.serial_data_input_pin = serial_data_input_pin
        self.shift_register_pin = shift_register_pin
        self.write_register_to_output_pin = write_register_to_output_pin
        self.register_active_pin = register_active_pin

        gpio.setup(self.output_disable_pin, gpio.OUT)
        gpio.setup(self.serial_data_input_pin, gpio.OUT)
        gpio.setup(self.shift_register_pin, gpio.OUT)
        gpio.setup(self.write_register_to_output_pin, gpio.OUT)
        gpio.setup(self.register_active_pin, gpio.OUT)

        # activate the register -- will have no effect if pin is hard-wired to 3.3v
        gpio.output(self.register_active_pin, gpio.HIGH)
