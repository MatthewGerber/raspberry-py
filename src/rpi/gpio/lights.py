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


class SevenSegmentWithDpLED(Component):

    class State(Component.State):

        def __init__(
                self,
                character: Optional[Union[int, str]]
        ):
            if character is not None and character not in SevenSegmentWithDpLED.CHARACTER_SEGMENTS:
                raise ValueError(f'Invalid character:  {character}')

            self.character = character

        def __eq__(
                self,
                other: object
        ) -> bool:

            if not isinstance(other, SevenSegmentWithDpLED.State):
                raise ValueError(f'Expected a {SevenSegmentWithDpLED.State}')

            return self.character == other.character

        def __str__(
                self
        ) -> str:

            return f'Value:  {self.character}'

    class Segment(Enum):
        A = auto()
        B = auto()
        C = auto()
        D = auto()
        E = auto()
        F = auto()
        G = auto()
        DECIMAL_POINT = auto()

    CHARACTER_SEGMENTS = {
        0: [],
        1: [],
        2: [],
        3: [],
        4: [],
        5: [],
        6: [],
        7: [],
        8: [],
        9: [],
        'A': [],
        'B': [],
        'C': [],
        'D': [],
        'E': [],
        'F': []
    }

    def set_state(
            self,
            state: 'Component.State'
    ):
        if not isinstance(state, SevenSegmentWithDpLED.State):
            raise ValueError(f'Expected a {SevenSegmentWithDpLED.State}')

        state: SevenSegmentWithDpLED.State

        segments = self.CHARACTER_SEGMENTS[state.character]

        shift_register_output_pins = list(sorted([
            self.segment_shift_register_output[segment]
            for segment in segments
        ]))



    def display(
            self,
            character: str
    ):
        self.set_state(SevenSegmentWithDpLED.State(character))

    def __init__(
            self,
            shift_register: ShiftRegister,
            segment_shift_register_output: Dict[Segment, int]
    ):
        super().__init__(SevenSegmentWithDpLED.State(None))

        self.shift_register = shift_register
        self.segment_shift_register_output = segment_shift_register_output
