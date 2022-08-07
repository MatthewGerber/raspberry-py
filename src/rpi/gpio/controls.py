from typing import List

import RPi.GPIO as gpio
import numpy as np

from rpi.gpio import Component
from rpi.gpio.adc import AdcDevice


class TwoPoleButton(Component):
    """
    A two-pole button switch.
    """

    class State(Component.State):
        """
        Button state.
        """

        def __init__(
                self,
                pressed: bool
        ):
            """
            Initialize the button state.

            :param pressed: Whether or not the button is pressed.
            """

            self.pressed = pressed

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, TwoPoleButton.State):
                raise ValueError(f'Expected a {TwoPoleButton.State}')

            return self.pressed == other.pressed

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'pressed={self.pressed}'

    def is_pressed(
            self
    ) -> bool:
        """
        Check whether the button is currently pressed.

        :return: True if pressed and False otherwise.
        """

        self.state: TwoPoleButton.State

        return self.state.pressed

    def __init__(
            self,
            input_pin: int,
            bounce_time_ms: int
    ):
        """
        Initialize the button.

        :param input_pin: Input pin for button.
        :param bounce_time_ms: Debounce interval (milliseconds).
        """

        super().__init__(
            state=TwoPoleButton.State(pressed=False)
        )

        self.input_pin = input_pin

        gpio.setup(input_pin, gpio.IN, pull_up_down=gpio.PUD_UP)

        gpio.add_event_detect(
            self.input_pin,
            gpio.BOTH,
            callback=lambda channel: self.set_state(
                TwoPoleButton.State(
                    pressed=gpio.input(self.input_pin) == gpio.LOW
                )
            ),
            bouncetime=bounce_time_ms
        )


class Joystick(Component):
    """
    Three-axis joystick:  left/right (X), up/down (Y), and depress (Z).
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                x: float,
                y: float,
                z: bool
        ):
            """
            Initialize the state.

            :param x: Left-right position [-1.0, 1.0].
            :param y: Up-down position [-1.0, 1.0]
            :param z: Whether or not the joystick is depressed.
            """

            self.x = x
            self.y = y
            self.z = z

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Joystick.State):
                raise ValueError(f'Expected a {Joystick.State}')

            return self.x == other.x and self.y == other.y and self.z == other.z

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'x: {self.x}, y: {self.y}, z: {self.z}'

    def update_state(
            self
    ):
        """
        Update state.
        """

        self.adc.update_state()

    def get_x(
            self
    ) -> float:
        """
        Get x-position of joystick.

        :return: x position.
        """

        self.update_state()

        state: Joystick.State = self.get_state()

        return state.x

    def get_y(
            self
    ) -> float:
        """
        Get y-position of joystick.

        :return: y position.
        """

        self.update_state()

        state: Joystick.State = self.get_state()

        return state.y

    def is_pressed(
            self
    ) -> bool:
        """
        Check whether the button is currently pressed.

        :return: True if pressed and False otherwise.
        """

        return self.button.is_pressed()

    def __init__(
            self,
            adc: AdcDevice,
            x_channel: int,
            y_channel: int,
            z_pin: int,
            invert_y: bool
    ):
        """
        Initialize the joystick.
        
        :param adc: Analog-to-digital converter.
        :param x_channel: Analog-to-digital channel on which to monitor x values.
        :param y_channel: Analog-to-digital channel on which to monitor y values.
        :param z_pin: GPIO pin used for z-axis switch.
        :param invert_y: Whether or not to invert y-axis values. If True, pushing the joystick forward will increase
        values and pulling it back will decrease values. If False, then the opposite will happen.
        """

        super().__init__(
            state=Joystick.State(0.0, 0.0, False)
        )

        self.adc = adc
        self.x_channel = x_channel
        self.y_channel = y_channel
        self.z_pin = z_pin
        self.invert_y = invert_y

        # create button on z pin and update joystick state when it gets pressed
        self.button = TwoPoleButton(
            input_pin=self.z_pin,
            bounce_time_ms=10
        )

        self.button.event(
            lambda s: self.set_state(
                Joystick.State(
                    x=self.adc.get_channel_value()[self.x_channel],
                    y=adc.invert_digital_value(
                        self.adc.get_channel_value()[self.y_channel],
                        self.y_channel
                    ) if self.invert_y else self.adc.get_channel_value()[self.y_channel],
                    z=s.pressed
                )
            )
        )

        # listen for events from the adc and update joystick state when they occur
        self.adc.event(
            lambda s: self.set_state(
                Joystick.State(
                    x=s.channel_value[self.x_channel],
                    y=adc.invert_digital_value(
                        s.channel_value[self.y_channel],
                        self.y_channel
                    ) if self.invert_y else s.channel_value[self.y_channel],
                    z=self.button.is_pressed()
                )
            )
        )


class MatrixKeypad(Component):
    """
    A matrix keypad.
    """

    class State(Component.State):
        """
        Keypad state.
        """

        def __init__(
                self,
                keys_pressed: np.ndarray
        ):
            """
            Initialize the state.

            :param keys_pressed: Keys that are pressed.
            """

            self.keys_pressed = keys_pressed

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, MatrixKeypad.State):
                raise ValueError(f'Expected a {MatrixKeypad.State}')

            return self.keys_pressed == other.keys_pressed

        def __str__(self) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Keys pressed:  {self.keys_pressed}'

    def scan(
            self
    ):
        key_matrix = np.empty_like(self.key_matrix)
        for col, scan_col_pin in enumerate(self.col_pins):

            for col_pin in self.col_pins:
                gpio.output(scan_col_pin, gpio.LOW if col_pin == scan_col_pin else gpio.HIGH)

            for row, scan_row_pin in enumerate(self.row_pins):
                row_pressed = not bool(gpio.input(scan_row_pin))
                key_matrix[row, col] = self.key_matrix[row, col] if row_pressed else None

        self.set_state(MatrixKeypad.State(key_matrix))

    def __init__(
            self,
            key_matrix: np.ndarray,
            row_pins: List[int],
            col_pins: List[int]
    ):
        """
        Initialize the keypad.

        :param key_matrix: Key matrix values.
        :param row_pins: Row pins, in order of bottom to top.
        :param col_pins: Column pins, in order of right to left.
        """

        pin_shape = (len(row_pins), len(col_pins))
        if key_matrix.shape != pin_shape:
            raise ValueError(f'Pin shape {pin_shape} does not match matrix shape {key_matrix.shape}')

        super().__init__(MatrixKeypad.State(np.empty_like(key_matrix)))

        self.key_matrix = key_matrix
        self.row_pins = row_pins
        self.col_pins = col_pins

        # read input from the rows
        for row_pin in self.row_pins:
            gpio.setup(row_pin, gpio.IN, pull_up_down=gpio.PUD_UP)

        # send output to the columns
        for col_pin in self.col_pins:
            gpio.setup(col_pin, gpio.OUT)
