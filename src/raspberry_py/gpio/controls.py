import time
from threading import Thread
from typing import List

import RPi.GPIO as gpio

from raspberry_py.gpio import Component
from raspberry_py.gpio.adc import AdcDevice


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
            bounce_time_ms: int,
            read_delay_ms: float
    ):
        """
        Initialize the button.

        :param input_pin: Input pin for button.
        :param bounce_time_ms: Debounce interval (milliseconds). Minimum time between event callbacks.
        :param read_delay_ms: Delay (milliseconds) between event callback and reading the GPIO value of the switch.
        """

        super().__init__(
            state=TwoPoleButton.State(pressed=False)
        )

        self.input_pin = input_pin

        gpio.setup(self.input_pin, gpio.IN, pull_up_down=gpio.PUD_UP)

        def read_after_delay(
                seconds: float
        ):
            """
            Read the input pin after a delay.

            :param seconds: Delay (s).
            """

            if seconds > 0.0:
                time.sleep(seconds)

            self.set_state(
                TwoPoleButton.State(
                    pressed=gpio.input(self.input_pin) == gpio.LOW
                )
            )

        # read after slight delay to let signal stabilize
        gpio.add_event_detect(
            self.input_pin,
            gpio.BOTH,
            callback=lambda channel: read_after_delay(read_delay_ms / 1000.0),
            bouncetime=bounce_time_ms
        )


class LimitSwitch(Component):
    """
    Contact-based limit switch.
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                pressed: bool
        ):
            """
            Initialize the state.

            :param pressed: Whether the switch is pressed.
            """

            self.pressed = pressed

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality.

            :param other: Other object.
            """

            if not isinstance(other, LimitSwitch.State):
                raise ValueError(f'Expected a {LimitSwitch.State}')

            return self.pressed == other.pressed

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Pressed:  {self.pressed}'

    def is_pressed(
            self
    ) -> bool:
        """
        Check whether the switch is currently pressed.

        :return: True if pressed and False otherwise.
        """

        self.state: LimitSwitch.State

        return self.state.pressed

    def __init__(
            self,
            input_pin: int,
            bounce_time_ms: int
    ):
        """
        Initialize the switch.

        :param input_pin: Input pin for switch.
        :param bounce_time_ms: Debounce interval (milliseconds).
        """

        self.input_pin = input_pin

        gpio.setup(self.input_pin, gpio.IN, pull_up_down=gpio.PUD_UP)

        super().__init__(
            state=LimitSwitch.State(
                pressed=gpio.input(self.input_pin) == gpio.LOW
             )
        )

        def read_after_delay(seconds: float):
            """
            Read the input pin after a delay.

            :param seconds: Delay (s).
            """

            time.sleep(seconds)
            self.set_state(
                LimitSwitch.State(
                    pressed=gpio.input(self.input_pin) == gpio.LOW
                )
            )

        # read after slight delay to let signal stabilize
        gpio.add_event_detect(
            self.input_pin,
            gpio.BOTH,
            callback=lambda channel: read_after_delay(0.05),
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
            bounce_time_ms=10,
            read_delay_ms=50
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
                key_matrix: List[List[str]]
        ):
            """
            Initialize the state.

            :param key_matrix: Key matrix.
            """

            self.key_matrix = key_matrix

            self.keys_pressed = sorted([
                value
                for row in self.key_matrix
                for value in row
                if value != ''
            ])

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

            return '\n'.join(
                '\t'.join(
                    '-' if v == '' else v
                    for v in row
                )
                for row in self.key_matrix
            )

    def scan_once(
            self
    ):
        """
        Scan the keypad once and update state accordingly.
        """

        key_matrix = self.empty(self.key_matrix)

        # scan each column
        for scan_col, scan_col_pin in enumerate(self.col_pins):

            # set the column low and check rows for low, indicating that the button has been pressed.
            gpio.output(scan_col_pin, gpio.LOW)
            for row, row_pin in enumerate(self.row_pins):
                if gpio.input(row_pin) == gpio.LOW:
                    key_matrix[row][scan_col] = self.key_matrix[row][scan_col]

            # set column back to high to scan next column
            gpio.output(scan_col_pin, gpio.HIGH)

        self.set_state(MatrixKeypad.State(key_matrix))

    def __scan_repeatedly__(
            self
    ):
        """
        Scan the keypad repeatedly and update state accordingly. This will continue to scan until `continue_scanning`
        becomes False. This is not intended to be called directly; instead, call `start_scanning` and `stop_scanning`.
        """

        while self.continue_scanning:
            self.scan_once()
            time.sleep(self.scan_sleep_seconds)

    def start_scanning(self):
        """
        Start scanning the keypad.
        """

        self.stop_scanning()
        self.continue_scanning = True
        self.scan_repeatedly_thread.start()

    def stop_scanning(self):
        """
        Stop scanning the keypad.
        """

        if self.scan_repeatedly_thread.is_alive():
            self.continue_scanning = False
            self.scan_repeatedly_thread.join()

    @staticmethod
    def empty(
            key_matrix: List[List[str]]
    ) -> List[List[str]]:
        """
        Create an empty key matrix like a reference.

        :param key_matrix: Reference keys.
        :return: Empty key matrix.
        """

        return [
            [''] * len(row)
            for row in key_matrix
        ]

    def __init__(
            self,
            key_matrix: List[List[str]],
            row_pins: List[int],
            col_pins: List[int],
            scans_per_second: int
    ):
        """
        Initialize the keypad.

        :param key_matrix: Key matrix values.
        :param row_pins: Row pins, in order of top to bottom of the keypad.
        :param col_pins: Column pins, in order of left to right of the keypad.
        :param scans_per_second: Number of scans per second.
        """

        if len(key_matrix) != len(row_pins):
            raise ValueError('Number of key matrix rows must equal number of row pins.')

        if not all(len(row) == len(col_pins) for row in key_matrix):
            raise ValueError('Number of columns in each row must equal number of column pins.')

        super().__init__(MatrixKeypad.State(self.empty(key_matrix)))

        self.key_matrix = key_matrix
        self.row_pins = row_pins
        self.col_pins = col_pins
        self.scans_per_second = scans_per_second

        self.scan_sleep_seconds = 1.0 / self.scans_per_second
        self.continue_scanning = True
        self.scan_repeatedly_thread = Thread(target=self.__scan_repeatedly__)

        # send output to the columns when scanning
        for col_pin in self.col_pins:
            gpio.setup(col_pin, gpio.OUT)
            gpio.output(col_pin, gpio.HIGH)

        # read input from the rows when scanning
        for row, row_pin in enumerate(self.row_pins):
            gpio.setup(row_pin, gpio.IN, pull_up_down=gpio.PUD_UP)
