import time
from typing import List, Optional

import RPi.GPIO as gpio

from rpi.gpio import Component


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
                other: 'LED.State'
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            return self.on == other.on

    def get(
            self
    ) -> 'LED.State':
        """
        Get the state.

        :return: State.
        """

        return self.state

    def set(
            self,
            state: 'LED.State'
    ):
        """
        Set the state and trigger any listeners.

        :param state: State.
        """

        super().set(state)

        self.state: 'LED.State'

        if self.state.on:
            gpio.output(self.output_pin, gpio.LOW if self.reverse else gpio.HIGH)
        else:
            gpio.output(self.output_pin, gpio.HIGH if self.reverse else gpio.LOW)

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

        self.set(self.state)


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
                other: 'LedBar.State'
        ) -> bool:
            """
            Check equality with another LED bar.

            :param other: Other LED bar.
            :return: True if equal and False otherwise.
            """

            return self.illuminated_led_index == other.illuminated_led_index

    def get(
            self
    ) -> 'LedBar.State':
        """
        Get the state.

        :return: State.
        """

        return self.state

    def flow(
            self
    ):
        """
        Flow light back and forth one time across the LED bar.
        """

        # turn all leds off
        for led in self.leds:
            led.set(LED.State(on=False))

        # illuminate the first led
        self.leds[0].set(LED.State(on=True))
        self.set(LedBar.State(self.leds[0], 0))

        # turn each led on in forward sequence
        for i in range(1, len(self.leds)):
            time.sleep(self.delay_seconds)
            self.leds[i - 1].set(LED.State(on=False))
            self.leds[i].set(LED.State(on=True))
            self.set(LedBar.State(self.leds[i], i))

        # turn each led on in reversed sequence
        for i in reversed(range(len(self.leds) - 1)):
            time.sleep(self.delay_seconds)
            self.leds[i + 1].set(LED.State(on=False))
            self.leds[i].set(LED.State(on=True))
            self.set(LedBar.State(self.leds[i], i))

    def __init__(
            self,
            output_pins: List[int],
            reverse: bool,
            delay_seconds: float
    ):
        """
        Initialize the LED bar.

        :param output_pins: Output pins in the order in which they are wired to GPIO ports.
        :param reverse: Whether or not the GPIO ports are wired to the cathodes of the LED bar.
        :param delay_seconds: How long to keep each LED on.
        """

        super().__init__(
            state=LedBar.State(None, None)
        )

        self.output_pins = output_pins
        self.reverse = reverse
        self.delay_seconds = delay_seconds

        self.leds = [
            LED(output_pin=pin, reverse=self.reverse)
            for pin in self.output_pins
        ]
