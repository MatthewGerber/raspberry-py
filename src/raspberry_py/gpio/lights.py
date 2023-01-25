import time
from datetime import timedelta
from enum import Enum, auto
from threading import Thread
from typing import List, Optional, Union, Dict, Tuple

import RPi.GPIO as gpio
import numpy as np
from rpi_ws281x import Adafruit_NeoPixel, Color

from raspberry_py.gpio import Component
from raspberry_py.gpio.integrated_circuits import ShiftRegister74HC595


class LED(Component):
    """
    LED.
    """

    class State(Component.State):
        """
        LED state.
        """

        def __init__(
                self,
                on: bool
        ):
            """
            Initialize the LED state.

            :param on: Whether or not the LED is on.
            """

            self.on = on

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, LED.State):
                raise ValueError(f'Expected a {LED.State}')

            return self.on == other.on

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'on={self.on}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state and trigger any listeners.

        :param state: State.
        """

        if not isinstance(state, LED.State):
            raise ValueError(f'Expected a {LED.State}')

        super().set_state(state)

        state: LED.State

        if state.on:
            gpio.output(self.output_pin, gpio.LOW if self.reverse else gpio.HIGH)
        else:
            gpio.output(self.output_pin, gpio.HIGH if self.reverse else gpio.LOW)

    def turn_on(
            self
    ):
        """
        Turn the LED on.
        """

        self.set_state(LED.State(on=True))

    def turn_off(
            self
    ):
        """
        Turn the LED off.
        """

        self.set_state(LED.State(on=False))

    def is_on(
            self
    ) -> bool:
        """
        Check whether the LED is on.

        :return: True if on and False otherwise.
        """

        self.state: LED.State

        return self.state.on

    def is_off(
            self
    ) -> bool:
        """
        Check whether the LED is off.

        :return: True if off and False otherwise.
        """

        return not self.is_on()

    def __init__(
            self,
            output_pin: int,
            reverse: bool = False
    ):
        """
        Initialize the LED.

        :param output_pin: Output pin that connects to the LED.
        :param reverse: Whether or not the LED is wired in reverse, such that LOW is on and HIGH is off.
        """

        super().__init__(
            state=LED.State(on=False)
        )

        self.output_pin = output_pin
        self.reverse = reverse

        gpio.setup(self.output_pin, gpio.OUT)

        self.set_state(self.state)


class LedBar(Component):
    """
    LED bar, with 10 integrated LEDs.
    """

    class State(Component.State):
        """
        LED bar state.
        """

        def __init__(
                self,
                illuminated_led: Optional[LED],
                illuminated_led_index: Optional[int]
        ):
            """
            Initialize the state.

            :param illuminated_led: LED that is illuminated.
            :param illuminated_led_index: Index of LED that is illuminated.
            """

            self.illuminated_led = illuminated_led
            self.illuminated_led_index = illuminated_led_index

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another LED bar.

            :param other: Other LED bar.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, LedBar.State):
                raise ValueError(f'Expected a {LedBar.State}')

            return self.illuminated_led_index == other.illuminated_led_index

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'illuminated={self.illuminated_led_index}'

    def flow(
            self,
            delay_seconds: float
    ):
        """
        Flow light back and forth one time across the LED bar.

        :param delay_seconds: How long to keep each LED on.
        """

        # turn all leds off
        for led in self.leds:
            led.turn_off()

        # illuminate the first led
        self.leds[0].turn_on()
        self.set_state(LedBar.State(self.leds[0], 0))

        # turn each led on in forward sequence
        for i in range(1, len(self.leds)):
            time.sleep(delay_seconds)
            self.leds[i - 1].turn_off()
            self.leds[i].turn_on()
            self.set_state(LedBar.State(self.leds[i], i))

        # turn each led on in reversed sequence
        for i in reversed(range(len(self.leds) - 1)):
            time.sleep(delay_seconds)
            self.leds[i + 1].turn_off()
            self.leds[i].turn_on()
            self.set_state(LedBar.State(self.leds[i], i))

        time.sleep(delay_seconds)
        self.leds[0].turn_off()
        self.set_state(LedBar.State(None, None))

    def turn_on(
            self,
            indices: Optional[List[int]] = None
    ):
        """
        Turn on LEDs.

        :param indices: LEDs to turn on, or None to turn all on.
        """

        if indices is None:
            indices = list(range(len(self.leds)))

        for i in indices:
            self.leds[i].turn_on()

    def turn_off(
            self,
            indices: Optional[List[int]] = None
    ):
        """
        Turn off LEDs.

        :param indices: LEDs to turn off, or None to turn all off.
        """

        if indices is None:
            indices = list(range(len(self.leds)))

        for i in indices:
            self.leds[i].turn_off()

    def __init__(
            self,
            output_pins: List[int],
            reverse: bool
    ):
        """
        Initialize the LED bar.

        :param output_pins: Output pins in the order in which they are wired to GPIO ports.
        :param reverse: Whether or not the GPIO ports are wired to the cathodes of the LED bar.
        """

        super().__init__(
            state=LedBar.State(None, None)
        )

        self.output_pins = output_pins
        self.reverse = reverse

        self.leds = [
            LED(output_pin=pin, reverse=self.reverse)
            for pin in self.output_pins
        ]

    def __len__(
            self
    ) -> int:
        """
        Get length (number of LEDs).

        :return: Length.
        """

        return len(self.leds)


class MulticoloredLED(Component):
    """
    Multicolored LED.
    """

    class State(Component.State):

        def __init__(
                self,
                r: float,
                g: float,
                b: float
        ):
            """
            Initialize the state.

            :param r: Red in [0.0, 100.0].
            :param g: Green in [0.0, 100.0].
            :param b: Blue in [0.0, 100.0].
            """

            self.r = r
            self.g = g
            self.b = b

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, MulticoloredLED.State):
                raise ValueError(f'Expected a {MulticoloredLED.State}')

            return self.r == other.r and self.g == other.g and self.b == other.b

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'r={self.r}, g={self.g}, b={self.b}'

    def set(
            self,
            r: float,
            g: float,
            b: float
    ):
        """
        Set color components.

        :param r: Red in [0.0, 100.0].
        :param g: Green in [0.0, 100.0].
        :param b: Blue in [0.0, 100.0].
        """

        # invert components for a common anode
        self.pwm_r.ChangeDutyCycle(100.0 - r if self.common_anode else r)
        self.pwm_g.ChangeDutyCycle(100.0 - g if self.common_anode else g)
        self.pwm_b.ChangeDutyCycle(100.0 - b if self.common_anode else b)
        self.set_state(MulticoloredLED.State(r=r, g=g, b=b))

    def __init__(
            self,
            r_pin: int,
            g_pin: int,
            b_pin: int,
            common_anode: bool
    ):
        """
        Initialize the LED.

        :param common_anode: True if the LED pins have a common anode (+) and False if thee pins have a common cathode
        (-).
        """

        super().__init__(MulticoloredLED.State(0.0, 0.0, 0.0))

        # create leds and their pulse-wave modulators
        self.led_r = LED(output_pin=r_pin)
        self.led_r.turn_on()
        self.pwm_r = gpio.PWM(self.led_r.output_pin, 2000)
        self.pwm_r.start(0)

        self.led_g = LED(output_pin=g_pin)
        self.led_g.turn_on()
        self.pwm_g = gpio.PWM(self.led_g.output_pin, 2000)
        self.pwm_g.start(0)

        self.led_b = LED(output_pin=b_pin)
        self.led_b.turn_on()
        self.pwm_b = gpio.PWM(self.led_b.output_pin, 2000)
        self.pwm_b.start(0)

        self.common_anode = common_anode


class SevenSegmentLedShiftRegister(Component):
    """
    A 7-segment LED driven by an 8-bit shift register.
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                character: Optional[Union[int, str]],
                decimal_point: bool
        ):
            """
            Initialize the state.

            :param character: Character.
            :param decimal_point: Show decimal point.
            """

            if character is not None and character not in SevenSegmentLedShiftRegister.CHARACTER_SEGMENTS:
                raise ValueError(f'Invalid character:  {character}')

            self.character = character
            self.decimal_point = decimal_point

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, SevenSegmentLedShiftRegister.State):
                raise ValueError(f'Expected a {SevenSegmentLedShiftRegister.State}')

            return self.character == other.character and self.decimal_point == other.decimal_point

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Value:  {self.character}{"." if self.decimal_point else ""}'

    # noinspection PyArgumentList
    class Segment(Enum):
        """
        LED segments.
        """

        A = auto()
        B = auto()
        C = auto()
        D = auto()
        E = auto()
        F = auto()
        G = auto()
        DECIMAL_POINT = auto()

    # mapping of display characters to led segments
    CHARACTER_SEGMENTS = {
        0: [Segment.A, Segment.B, Segment.C, Segment.D, Segment.E, Segment.F],
        1: [Segment.B, Segment.C],
        2: [Segment.A, Segment.B, Segment.G, Segment.E, Segment.D],
        3: [Segment.A, Segment.B, Segment.G, Segment.C, Segment.D],
        4: [Segment.F, Segment.G, Segment.B, Segment.C],
        5: [Segment.A, Segment.F, Segment.G, Segment.C, Segment.D],
        6: [Segment.A, Segment.F, Segment.E, Segment.D, Segment.C, Segment.G],
        7: [Segment.A, Segment.B, Segment.C],
        8: [Segment.A, Segment.F, Segment.G, Segment.C, Segment.D, Segment.E, Segment.B],
        9: [Segment.A, Segment.F, Segment.G, Segment.B, Segment.C],
        'A': [Segment.A, Segment.F, Segment.E, Segment.G, Segment.B, Segment.C],
        'b': [Segment.F, Segment.E, Segment.G, Segment.C, Segment.D],
        'C': [Segment.A, Segment.F, Segment.E, Segment.D],
        'd': [Segment.B, Segment.C, Segment.G, Segment.E, Segment.D],
        'E': [Segment.A, Segment.F, Segment.E, Segment.D, Segment.G],
        'F': [Segment.F, Segment.E, Segment.A, Segment.G]
    }

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, SevenSegmentLedShiftRegister.State):
            raise ValueError(f'Expected a {SevenSegmentLedShiftRegister.State}')

        state: SevenSegmentLedShiftRegister.State

        # get segments for display character
        segments = self.CHARACTER_SEGMENTS[state.character]

        # add segment for decimal point if needed
        if state.decimal_point:
            segments.append(SevenSegmentLedShiftRegister.Segment.DECIMAL_POINT)

        # get shift register pins that should be turned on for segments
        shift_register_output_pins = list([
            self.segment_shift_register_output[segment]
            for segment in segments
        ])

        # get bit string for shift register pins with msb on left. 0 (low) will have the effect of turning the segment
        # on, and 1 (high) will have the effect of turning the segment off.
        bit_string = ''.join(reversed([
            '0' if i in shift_register_output_pins else '1'
            for i in range(self.shift_register.bits)
        ]))

        # write integer for bit string to shift register
        bit_string_int = int(bit_string, 2)
        self.shift_register.write(bit_string_int)

    def display(
            self,
            character: str,
            decimal_point: bool
    ):
        """
        Display a character on the LED.

        :param character: Character.
        :param decimal_point: Whether to show the decimal point.
        """

        self.set_state(SevenSegmentLedShiftRegister.State(character, decimal_point))

    def __init__(
            self,
            shift_register: ShiftRegister74HC595,
            segment_shift_register_output: Dict[Segment, int]
    ):
        """
        Initialize the LED.

        :param shift_register: Shift register (must be at least 8 bits).
        :param segment_shift_register_output: Mapping of LED segments to shift-register output lines.
        """

        if shift_register.bits < 8:
            raise ValueError(f'Expected a shift register with at least 8 bits but got one with {shift_register.bits}.')

        super().__init__(SevenSegmentLedShiftRegister.State(None, False))

        self.shift_register = shift_register
        self.segment_shift_register_output = segment_shift_register_output


class FourDigitSevenSegmentLED(Component):
    """
    A four-digit, seven-segment LED driven by a cycling shift register.
    """

    class State(Component.State):
        """
        State.
        """

        def get(
                self,
                led_idx: int
        ) -> Tuple[Optional[Union[int, str]], bool]:
            """
            Get the character and decimal boolean for an LED.

            :param led_idx: LED index.
            :return: 2-tuple of character and decimal boolean.
            """

            if led_idx == 0:
                return self.character_0, self.decimal_point_0
            elif led_idx == 1:
                return self.character_1, self.decimal_point_1
            elif led_idx == 2:
                return self.character_2, self.decimal_point_2
            elif led_idx == 3:
                return self.character_3, self.decimal_point_3
            else:
                raise ValueError(f'Invalid LED index:  {led_idx}')

        def __init__(
                self,
                character_0: Optional[Union[int, str]],
                decimal_point_0: bool,
                character_1: Optional[Union[int, str]],
                decimal_point_1: bool,
                character_2: Optional[Union[int, str]],
                decimal_point_2: bool,
                character_3: Optional[Union[int, str]],
                decimal_point_3: bool
        ):
            """
            Initialize the state.

            :param character_0: Character 0.
            :param decimal_point_0: Show decimal point.
            :param character_1: Character 1.
            :param decimal_point_1: Show decimal point.
            :param character_2: Character 2.
            :param decimal_point_2: Show decimal point.
            :param character_3: Character 3.
            :param decimal_point_3: Show decimal point.
            """

            self.character_0 = character_0
            self.decimal_point_0 = decimal_point_0
            self.character_1 = character_1
            self.decimal_point_1 = decimal_point_1
            self.character_2 = character_2
            self.decimal_point_2 = decimal_point_2
            self.character_3 = character_3
            self.decimal_point_3 = decimal_point_3

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, FourDigitSevenSegmentLED.State):
                raise ValueError(f'Expected a {FourDigitSevenSegmentLED.State}')

            return self.character_0 == other.character_0 and self.decimal_point_0 == other.decimal_point_0 and self.character_1 == other.character_1 and self.decimal_point_1 == other.decimal_point_1 and self.character_2 == other.character_2 and self.decimal_point_2 == other.decimal_point_2 and self.character_3 == other.character_3 and self.decimal_point_3 == other.decimal_point_3

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Value:  {self.character_0}{"." if self.decimal_point_0 else ""}{self.character_1}{"." if self.decimal_point_1 else ""}{self.character_2}{"." if self.decimal_point_2 else ""}{self.character_3}{"." if self.decimal_point_3 else ""}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, FourDigitSevenSegmentLED.State):
            raise ValueError(f'Expected a {FourDigitSevenSegmentLED.State}')

        super().set_state(state)

        self.stop_display_thread()

        # start a new display thread
        self.run_display_thread = True
        self.display_thread = Thread(target=self.display_thread_target)
        self.display_thread.start()

    def display_thread_target(
            self
    ):
        """
        Cycles the transistor base pins to display the current state.
        """

        self.state: FourDigitSevenSegmentLED.State

        led = 0
        while self.run_display_thread:

            # activate the current led by setting its associated transistor base pin to low and all other transistor
            # base pins to high. they're pnp transistors, and low will send high current to the associated led anode.
            for pin_idx, pin in enumerate(self.led_transistor_base_pins):
                if pin_idx == led:
                    gpio.output(pin, gpio.LOW)
                else:
                    gpio.output(pin, gpio.HIGH)

            # display the current led's character and decimal point via the shift register
            self.led_shift_register.display(*self.state.get(led))

            # hold the current led for a duration
            time.sleep(self.led_display_time.total_seconds())

            # advance to the next led
            led = (led + 1) % len(self.led_transistor_base_pins)

    def display(
            self,
            character_0: str,
            decimal_point_0: bool,
            character_1: str,
            decimal_point_1: bool,
            character_2: str,
            decimal_point_2: bool,
            character_3: str,
            decimal_point_3: bool
    ):
        """
        Display characters and decimal points on the LED.

        :param character_0: Character 0.
        :param decimal_point_0: Whether to show the decimal point.
        :param character_1: Character 1.
        :param decimal_point_1: Whether to show the decimal point.
        :param character_2: Character 2.
        :param decimal_point_2: Whether to show the decimal point.
        :param character_3: Character 3.
        :param decimal_point_3: Whether to show the decimal point.
        """

        self.set_state(FourDigitSevenSegmentLED.State(
            character_0,
            decimal_point_0,
            character_1,
            decimal_point_1,
            character_2,
            decimal_point_2,
            character_3,
            decimal_point_3
        ))

    def stop_display_thread(
            self
    ):
        """
        Stop the display thread.
        """

        if self.display_thread is not None:
            self.run_display_thread = False
            self.display_thread.join()

    def __init__(
            self,
            led_0_transistor_base_pin: int,
            led_1_transistor_base_pin: int,
            led_2_transistor_base_pin: int,
            led_3_transistor_base_pin: int,
            led_shift_register: SevenSegmentLedShiftRegister,
            led_display_time: timedelta
    ):
        """
        Initialize the LED.

        :param led_0_transistor_base_pin: Base pin 0.
        :param led_1_transistor_base_pin: Base pin 1.
        :param led_2_transistor_base_pin: Base pin 2.
        :param led_3_transistor_base_pin: Base pin 3.
        :param led_shift_register: Shift register for generating outputs for a single 7-segment LED.
        :param led_display_time: Amount of time to hold each 7-segment LED.
        """

        super().__init__(FourDigitSevenSegmentLED.State(None, False, None, False, None, False, None, False))

        self.led_0_transistor_base_pin = led_0_transistor_base_pin
        self.led_1_transistor_base_pin = led_1_transistor_base_pin
        self.led_2_transistor_base_pin = led_2_transistor_base_pin
        self.led_3_transistor_base_pin = led_3_transistor_base_pin
        self.led_shift_register = led_shift_register
        self.led_display_time = led_display_time

        self.display_thread = None
        self.run_display_thread = False
        self.led_transistor_base_pins = [
            self.led_0_transistor_base_pin,
            self.led_1_transistor_base_pin,
            self.led_2_transistor_base_pin,
            self.led_3_transistor_base_pin
        ]

        for led_transistor_base_pin in self.led_transistor_base_pins:
            gpio.setup(led_transistor_base_pin, gpio.OUT)


class LedMatrix(Component):
    """
    LED matrix.
    """

    # 8x8 array of bit values that displays a smiling face
    SMILE_8x8 = np.array([
        [0, 0, 1, 1, 1, 1, 0, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [1, 0, 1, 0, 0, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 0, 0, 1, 0, 1],
        [0, 1, 0, 1, 1, 0, 1, 0],
        [0, 0, 1, 0, 0, 1, 0, 0],
        [0, 0, 0, 1, 1, 0, 0, 0]
    ])

    # 8x8 array of bit values that displays an A
    A_8x8 = np.array([
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0]
    ])

    class State(Component.State):
        """
        LED matrix state.
        """

        def __init__(
                self,
                frame: np.ndarray
        ):
            """
            Initialize the state.

            :param frame: Frame to display. Values must be able to cast to int.
            """

            self.frame = frame

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, LedMatrix.State):
                raise ValueError(f'Expected a {LedMatrix.State}')

            return np.all(self.frame == other.frame)

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'{self.frame}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, LedMatrix.State):
            raise ValueError(f'Expected a {LedMatrix.State}')

        super().set_state(state)

        self.stop_display_thread()

        # start a new display thread
        self.run_display_thread = True
        self.display_thread = Thread(target=self.display_thread_target)
        self.display_thread.start()

    def display_thread_target(
            self
    ):
        """
        Cycles over columns and displays each in turn.
        """

        self.state: LedMatrix.State

        num_cols = self.state.frame.shape[1]
        while self.run_display_thread:

            # scan across columns, displaying each in turn for the given delay.
            for col in range(num_cols):

                # build binary string that sets only the current column to low to enable its row inputs, which will be
                # high. convert the binary string to an integer for input to the shift register.
                col_value = int(''.join('0' if i == col else '1' for i in range(num_cols)), 2)

                # build binary string that sets the current column's rows to high (on) or low (low) according to the
                # frame. convert the binary string to an integer for input to the shift register.
                row_value = int(''.join(str(int(v)) for v in self.state.frame[:, col]), 2)

                # write the row then the column. the circuit contains two shift registers in series. the first value
                # (row) will end up in the second shift register, and the second (column) will end up in the first shift
                # register.
                self.shift_register.write([row_value, col_value])

                # hold for a delay
                time.sleep(self.frame_scan_delay.total_seconds())

    def display(
            self,
            frame: np.ndarray
    ):
        """
        Display a frame.

        :param frame: Frame. Must be a (self.rows, self.cols) dimensional array of values that can be cast to 0/1.
        """

        if frame.shape != (self.rows, self.cols):
            raise ValueError(f'Display frames must have shape ({self.rows},{self.cols}).')

        self.set_state(LedMatrix.State(frame))

    def stop_display_thread(
            self
    ):
        """
        Stop the display thread.
        """

        if self.display_thread is not None:
            self.run_display_thread = False
            self.display_thread.join()

    def __init__(
            self,
            rows: int,
            cols: int,
            shift_register: ShiftRegister74HC595,
            frame_scan_delay: timedelta
    ):
        """
        Initialize the matrix.

        :param rows: Number of rows.
        :param cols: Number of columns.
        :param shift_register: Shift register. The circuit is assumed to contain two shift registers connected in
        series such that only a single instance is required. See the led_matrix.py example and associated circuit in the
        tutorial.
        :param frame_scan_delay: Interval of time to display each column when scanning the matrix.
        """

        super().__init__(LedMatrix.State(np.zeros((rows, cols), dtype=int)))

        self.rows = rows
        self.cols = cols
        self.shift_register = shift_register
        self.frame_scan_delay = frame_scan_delay

        self.display_thread = None
        self.run_display_thread = False


class LedStrip:
    """
    LED strip, controlled by a WS281x driver and single-GPIO pin PWM.
    """

    def __init__(
            self,
            led_count: int = 8,
            led_pin: int = 18,
            led_freq_hz: int = 800000,
            led_dma: int = 10,
            led_brightness: int = 255,
            led_invert: int = False,
            led_channel: int = 0
    ):
        """
        Initialize the strip.

        :param led_count: Number of LED pixels.
        :param led_pin: GPIO pin connected to the pixels (18 uses PWM).
        :param led_freq_hz: LED signal frequency in hertz (usually 800khz).
        :param led_dma: DMA channel to use for generating signal (try 10).
        :param led_brightness: Set to 0 for darkest and 255 for brightest.
        :param led_invert: True to invert the signal (when using NPN transistor level shift).
        :param led_channel: Set to '1' for GPIOs 13, 19, 41, 45 or 53
        """

        self.order = 'RGB'

        self.strip = Adafruit_NeoPixel(
            led_count,
            led_pin,
            led_freq_hz,
            led_dma,
            led_invert,
            led_brightness,
            led_channel
        )

        self.strip.begin()

    def get_color(
            self,
            rgb: int
    ) -> Color:
        """
        Get color.

        :param rgb: Color integer.
        :return: Color.
        """

        b = rgb & 255
        g = rgb >> 8 & 255
        r = rgb >> 16 & 255
        led_type = ['GRB', 'GBR', 'RGB', 'RBG', 'BRG', 'BGR']
        color = [Color(g, r, b), Color(g, b, r), Color(r, g, b), Color(r, b, g), Color(b, r, g), Color(b, g, r)]

        return color[led_type.index(self.order)]

    def color_wipe(
            self,
            rgb: int,
            wait_ms: int = 50
    ):
        """
        Wipe color across display a pixel at a time.

        :param rgb: Color.
        :param wait_ms: Delay.
        """

        color = self.get_color(rgb)
        for i in range(self.strip.numPixels()):
            self.strip.setPixelColor(i, color)
            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def theater_chase(
            self,
            color: Color,
            wait_ms: int = 50,
            iterations: int = 10
    ):
        """
        Movie theater light style chaser animation.

        :param color: Color.
        :param wait_ms: Delay.
        :param iterations: Iterations.
        """

        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, color)
                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, 0)

    @staticmethod
    def wheel(
            pos: int
    ) -> Color:
        """
        Generate rainbow colors.

        :param pos: Position in [0,255].
        :return: Color.
        """

        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = pos * 3
            g = 255 - pos * 3
            b = 0
        elif pos < 170:
            pos -= 85
            r = 255 - pos * 3
            g = 0
            b = pos * 3
        else:
            pos -= 170
            r = 0
            g = pos * 3
            b = 255 - pos * 3

        return Color(r, g, b)

    def rainbow(
            self,
            wait_ms: int = 20,
            iterations: int = 1
    ):
        """
        Draw rainbow that fades across all pixels at once.

        :param wait_ms: Delay.
        :param iterations: Iterations.
        """

        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel((i + j) & 255))

            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def rainbow_cycle(
            self,
            wait_ms: int = 20,
            iterations: int = 5
    ):
        """
        Draw rainbow that uniformly distributes itself across all pixels.

        :param wait_ms: Delay.
        :param iterations: Iterations.
        """

        for j in range(256 * iterations):
            for i in range(self.strip.numPixels()):
                self.strip.setPixelColor(i, self.wheel((int(i * 256 / self.strip.numPixels()) + j) & 255))

            self.strip.show()
            time.sleep(wait_ms / 1000.0)

    def theater_chase_rainbow(
            self,
            wait_ms: int = 50
    ):
        """
        Rainbow movie theater light style chaser animation.

        :param wait_ms: Delay.
        """

        for j in range(256):
            for q in range(3):

                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, self.wheel((i + j) % 255))

                self.strip.show()
                time.sleep(wait_ms / 1000.0)
                for i in range(0, self.strip.numPixels(), 3):
                    self.strip.setPixelColor(i + q, 0)

    def set_led(
            self,
            index: int,
            r: int,
            g: int,
            b: int
    ):
        """
        Set LED.

        :param index: LED index.
        :param r: Red.
        :param g: Green.
        :param b: Blue.
        """

        color = Color(r, g, b)
        for i in range(8):
            if index & 0x01 == 1:
                self.strip.setPixelColor(i, color)
                self.strip.show()

            index = index >> 1
