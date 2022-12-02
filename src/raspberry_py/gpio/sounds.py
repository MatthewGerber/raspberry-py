import math
import time
from datetime import timedelta
from typing import Optional

import RPi.GPIO as gpio

from raspberry_py.gpio import Component


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

        if not isinstance(state, ActiveBuzzer.State):
            raise ValueError(f'Expected a {ActiveBuzzer.State}')

        super().set_state(state)

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


class PassiveBuzzer(Component):
    """
    Passive buzzer, driven by PWM.
    """

    class State(Component.State):
        """
        State.
        """

        def __init__(
                self,
                frequency: float
        ):
            """
            Initialize the state.

            :param frequency: Frequency.
            """

            self.frequency = frequency

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, PassiveBuzzer.State):
                raise ValueError(f'Expected a {PassiveBuzzer.State}')

            return self.frequency == other.frequency

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'frequency={self.frequency}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state.

        :param state: State.
        """

        if not isinstance(state, PassiveBuzzer.State):
            raise ValueError(f'Expected a {PassiveBuzzer.State}')

        super().set_state(state)

        state: PassiveBuzzer.State

        rad_frac = 100.0 - state.frequency  # 0.0 is highest and 1.0 is lowest
        pwm_frequency = 2000.0 + math.cos(rad_frac * math.pi) * 500.0
        self.pwm.ChangeFrequency(pwm_frequency)

    def start(
            self,
            frequency: float
    ):
        """
        Start the buzzer.

        :param frequency: Frequency.
        """

        self.pwm.start(50)
        self.set_state(PassiveBuzzer.State(frequency=frequency))

    def set_frequency(
            self,
            frequency: float
    ):
        """
        Set buzzer frequency.

        :param frequency: Frequency, as fraction of the buzzer's dynamic range.
        """

        self.set_state(PassiveBuzzer.State(frequency=frequency))

    def stop(
            self
    ):
        """
        Stop buzzing.
        """

        self.pwm.stop()

    def __init__(
            self,
            output_pin: int
    ):
        """
        Initialize the buzzer.

        :param output_pin: Output pin.
        """

        self.frequency = 0.0

        super().__init__(
            state=PassiveBuzzer.State(frequency=self.frequency)
        )

        self.output_pin = output_pin
        gpio.setup(self.output_pin, gpio.OUT)

        self.pwm = gpio.PWM(self.output_pin, 1)
