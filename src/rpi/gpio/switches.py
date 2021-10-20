import RPi.GPIO as gpio

from rpi.gpio import Component


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
                TwoPoleButton.State(pressed=True)
            ) if gpio.input(self.input_pin) == gpio.LOW else
            self.set_state(
                TwoPoleButton.State(pressed=False)
            ) if gpio.input(self.input_pin) == gpio.HIGH else
            None,
            bouncetime=bounce_time_ms
        )
