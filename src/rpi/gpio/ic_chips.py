from typing import Optional

import RPi.GPIO as gpio

from rpi.gpio import Component


class ShiftRegister8Bit(Component):
    """
    8-bit shift register for serial-to-parallel data. Compatible with the 74HC595 IC (see datasheet in docs).
    """

    class State(Component.State):

        def __init__(
                self,
                enabled: bool,
                x: Optional[int]
        ):
            bit_length = x.bit_length()
            if bit_length > 8:
                raise ValueError(f'Cannot write {bit_length} bits to an 8-bit shift register.')

            self.enabled = enabled
            self.x = x

        def __eq__(
                self,
                other: object
        ) -> bool:

            if not isinstance(other, ShiftRegister8Bit.State):
                raise ValueError(f'Expected a {ShiftRegister8Bit.State}')

            return self.enabled == other.enabled and self.x == other.x

        def __str__(
                self
        ) -> str:

            return f'Enabled:  {self.enabled}, Value:  {self.x}'

    def set_state(
            self,
            state: 'Component.State'
    ):
        if not isinstance(state, ShiftRegister8Bit.State):
            raise ValueError(f'Expected a {ShiftRegister8Bit.State}')

        super().set_state(state)

        state: ShiftRegister8Bit.State

        gpio.output(self.output_enable_pin, gpio.LOW if state.enabled else gpio.HIGH)

        # clear register
        self.clear()

        # write serial bits to parallel output if we have a value
        if state.x is not None:

            for bit_idx in range(state.x.bit_length()):
                bit_value = (state.x >> bit_idx) & 1
                gpio.output(self.shift_register_pin, gpio.LOW)
                gpio.output(self.serial_data_input_pin, gpio.HIGH if bit_value == 1 else gpio.LOW)
                gpio.output(self.shift_register_pin, gpio.HIGH)

            gpio.output(self.write_register_to_output_pin, gpio.HIGH)

    def enable(
            self
    ):
        self.state: ShiftRegister8Bit.State
        self.set_state(ShiftRegister8Bit.State(True, self.state.x))

    def disable(
            self
    ):
        self.state: ShiftRegister8Bit.State
        self.set_state(ShiftRegister8Bit.State(True, self.state.x))

    def write(
            self,
            x: int
    ):
        self.state: ShiftRegister8Bit.State
        self.set_state(ShiftRegister8Bit.State(self.state.enabled, x))

    def clear(
            self
    ):
        """
        Clear the shift register.
        """

        gpio.output(self.serial_data_input_pin, gpio.LOW)
        gpio.output(self.shift_register_pin, gpio.LOW)
        gpio.output(self.write_register_to_output_pin, gpio.LOW)
        gpio.output(self.register_reset_pin, gpio.LOW)
        gpio.output(self.register_reset_pin, gpio.HIGH)

    def __init__(
            self,
            output_enable_pin: int,
            serial_data_input_pin: int,
            shift_register_pin: int,
            write_register_to_output_pin: int,
            register_reset_pin: int
    ):
        super().__init__(ShiftRegister8Bit.State(False, None))

        self.output_enable_pin = output_enable_pin
        self.serial_data_input_pin = serial_data_input_pin
        self.shift_register_pin = shift_register_pin
        self.write_register_to_output_pin = write_register_to_output_pin
        self.register_reset_pin = register_reset_pin

        gpio.setup(self.output_enable_pin, gpio.OUT)
        gpio.setup(self.serial_data_input_pin, gpio.OUT)
        gpio.setup(self.shift_register_pin, gpio.OUT)
        gpio.setup(self.write_register_to_output_pin, gpio.OUT)
        gpio.setup(self.register_reset_pin, gpio.OUT)
