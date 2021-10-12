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
                other: 'TwoPoleButton.State'
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            return self.pressed == other.pressed

    def get(
            self
    ) -> 'TwoPoleButton.State':
        """
        Get the state.

        :return: State.
        """

        return self.state

    def update(
            self
    ):
        """
        Update the state based on the input channel's value.
        """

        self.set(TwoPoleButton.State(pressed=True if gpio.input(self.input_pin) == gpio.LOW else False))

    def __init__(
            self,
            input_pin: int
    ):
        """
        Initialize the button.

        :param input_pin: Input pin for button.
        """

        super().__init__(
            state=TwoPoleButton.State(pressed=False)
        )

        self.input_pin = input_pin

        gpio.setup(input_pin, gpio.IN, pull_up_down=gpio.PUD_UP)
