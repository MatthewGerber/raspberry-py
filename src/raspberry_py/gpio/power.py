import RPi.GPIO as gpio

from raspberry_py.gpio import Component, CkPin


class Relay(Component):
    """
    An electromagnetic relay switch, used to control a high-current circuit with a low-power circuit. See the example
    circuit shown on page 176 of the tutorial in which a relay is used to power a direct-current motor.
    """

    class State(Component.State):
        """
        Relay state.
        """

        def __init__(
                self,
                closed: bool
        ):
            """
            Initialize the state.

            :param closed: Whether the relay's internal switch is closed.
            """

            self.closed = closed

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check whether the current state equals another.

            :param other: Other state.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Relay.State):
                raise ValueError(f'Expected a {Relay.State}')

            return self.closed == other.closed

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Closed:  {self.closed}'

    def set_state(
            self,
            state: State
    ):
        """
        Set the current state.

        :param state: State.
        """

        state: Relay.State

        gpio.output(self.transistor_base_pin, gpio.HIGH if state.closed else gpio.LOW)

        super().set_state(state)

    def close(self):
        """
        Close the relay.
        """

        self.set_state(Relay.State(closed=True))

    def open(self):
        """
        Open the relay.
        """

        self.set_state(Relay.State(closed=False))

    def __init__(
            self,
            transistor_base_pin: CkPin
    ):
        """
        Initialize the relay.

        :param transistor_base_pin: GPIO port connected to the base bin of the transistor to which the relay is
        connected.
        """

        super().__init__(Relay.State(closed=False))

        self.transistor_base_pin = transistor_base_pin
        gpio.setup(self.transistor_base_pin, gpio.OUT)
        gpio.output(self.transistor_base_pin, gpio.LOW)
