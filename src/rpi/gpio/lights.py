import time
from enum import Enum, auto
from typing import List, Optional, Union, Dict

import RPi.GPIO as gpio

from rpi.gpio import Component
from rpi.gpio.ic_chips import ShiftRegister


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
            state: 'Component.State'
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

        # get bit string for shift register pins with msb on left
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
            shift_register: ShiftRegister,
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
