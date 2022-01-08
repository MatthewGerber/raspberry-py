from typing import Optional

import RPi.GPIO as gpio

from rpi.gpio import Component


class ShiftRegister(Component):
    """
    Shift register for serial-to-parallel data conversion. Compatible with the 74HC595 IC (see datasheet in docs).
    """

    class State(Component.State):

        def __init__(
                self,
                enabled: bool,
                x: Optional[int]
        ):
            self.enabled = enabled
            self.x = x

        def __eq__(
                self,
                other: object
        ) -> bool:

            if not isinstance(other, ShiftRegister.State):
                raise ValueError(f'Expected a {ShiftRegister.State}')

            return self.enabled == other.enabled and self.x == other.x

        def __str__(
                self
        ) -> str:

            return f'Enabled:  {self.enabled}, Value:  {self.x}'

    def set_state(
            self,
            state: 'Component.State'
    ):
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

            for bit_idx in range(self.bits):
                bit_value = (state.x >> bit_idx) & 1
                gpio.output(self.shift_register_pin, gpio.LOW)
                gpio.output(self.serial_data_input_pin, gpio.HIGH if bit_value == 1 else gpio.LOW)
                gpio.output(self.shift_register_pin, gpio.HIGH)

            gpio.output(self.write_register_to_output_pin, gpio.HIGH)

        super().set_state(state)

    def enable(
            self
    ):
        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(True, self.state.x))

    def disable(
            self
    ):
        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(False, self.state.x))

    def write(
            self,
            x: int
    ):
        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(self.state.enabled, x))

    def clear(
            self
    ):
        """
        Clear the shift register.
        """

        self.state: ShiftRegister.State
        self.set_state(ShiftRegister.State(self.state.enabled, 0))

    def __init__(
            self,
            bits: int,
            output_disable_pin: int,
            serial_data_input_pin: int,
            shift_register_pin: int,
            write_register_to_output_pin: int,
            register_reset_pin: int
    ):
        super().__init__(ShiftRegister.State(False, None))

        self.bits = bits
        self.output_disable_pin = output_disable_pin
        self.serial_data_input_pin = serial_data_input_pin
        self.shift_register_pin = shift_register_pin
        self.write_register_to_output_pin = write_register_to_output_pin
        self.register_reset_pin = register_reset_pin

        gpio.setup(self.output_disable_pin, gpio.OUT)
        gpio.setup(self.serial_data_input_pin, gpio.OUT)
        gpio.setup(self.shift_register_pin, gpio.OUT)
        gpio.setup(self.write_register_to_output_pin, gpio.OUT)
        gpio.setup(self.register_reset_pin, gpio.OUT)

        # gpio.output(self.register_reset_pin, gpio.HIGH)
