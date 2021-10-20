import time
from datetime import timedelta
from typing import Optional

import RPi.GPIO as gpio

from rpi.gpio import Component


class ActiveBuzzer(Component):
    """
    Active buzzer.
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                on: bool
        ):
            """
            Initialize the state.

            :param on: Whether or not the buzzer is on.
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

            if not isinstance(other, ActiveBuzzer.State):
                raise ValueError(f'Expected a {ActiveBuzzer.State}')

            return self.on == other.on

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'buzzing={self.on}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state.

        :param state: State.
        """

        super().set_state(state)

        if not isinstance(state, ActiveBuzzer.State):
            raise ValueError(f'Expected a {ActiveBuzzer.State}')

        state: ActiveBuzzer.State

        if state.on:
            gpio.output(self.output_pin, gpio.HIGH)
        else:
            gpio.output(self.output_pin, gpio.LOW)

    def buzz(
            self,
            duration: Optional[timedelta] = None
    ):
        """
        Start buzzing.

        :param duration: Duration to buzz, or None to buzz until `stop` is called.
        """

        self.set_state(ActiveBuzzer.State(on=True))

        if duration is not None:
            time.sleep(duration.total_seconds())
            self.set_state(ActiveBuzzer.State(on=False))

    def stop(
            self
    ):
        """
        Stop buzzing.
        """

        self.set_state(ActiveBuzzer.State(on=False))

    def __init__(
            self,
            output_pin: int
    ):
        """
        Initialize the buzzer.

        :param output_pin: Output pin.
        """

        super().__init__(
            state=ActiveBuzzer.State(on=False)
        )

        self.output_pin = output_pin

        gpio.setup(self.output_pin, gpio.OUT)
