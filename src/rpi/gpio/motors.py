import RPi.GPIO as gpio

from rpi.gpio import Component


class DcMotor(Component):
    """
    DC motor.
    """

    class State(Component.State):
        """
        DC motor state.
        """

        def __init__(
                self,
                speed: int
        ):
            """
            Initialize the state.

            :param speed: Speed.
            """

            self.speed = speed

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another object.

            :param other: Other object.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, DcMotor.State):
                raise ValueError(f'Expected a {DcMotor.State}')

            return self.speed == other.speed

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Speed:  {self.speed}'

    def set_state(
            self,
            state: Component.State
    ):
        """
        Set the state.

        :param state: State.
        """

        if not isinstance(state, DcMotor.State):
            raise ValueError(f'Expected a {DcMotor.State}')

        super().set_state(state)

        state: DcMotor.State

        # negative speed rotates one direction
        if state.speed < 0:
            gpio.output(self.in_1_pin, gpio.HIGH)
            gpio.output(self.in_2_pin, gpio.LOW)

        # positive speed rotates in the other direction
        elif state.speed > 0:
            gpio.output(self.in_1_pin, gpio.LOW)
            gpio.output(self.in_2_pin, gpio.HIGH)
        else:
            gpio.output(self.in_1_pin, gpio.LOW)
            gpio.output(self.in_2_pin, gpio.LOW)

        # update pwm
        self.pwm_enable.ChangeDutyCycle(abs(state.speed))

    def start(
            self
    ):
        """
        Start the motor at the current speed.
        """

        self.state: DcMotor.State

        self.pwm_enable.start(self.state.speed)

    def stop(
            self
    ):
        """
        Stop the motor.
        """

        self.pwm_enable.stop()

    def set_speed(
            self,
            speed: int
    ):
        """
        Set the motor's speed.

        :param speed: Speed (in [-100,+100]).
        """

        self.set_state(DcMotor.State(speed))

    def __init__(
            self,
            enable_pin: int,
            in_1_pin: int,
            in_2_pin: int,
            speed: int
    ):
        """
        Initialize the motor.

        :param enable_pin: GPIO pin connected to the enable pin of the L293D IC.
        :param in_1_pin: GPIO pin connected to the in-1 pin of the L293D IC.
        :param in_2_pin: GPIO pin connected to the in-2 pin of the L293D IC.
        :param speed: Initial motor speed (in [-100,+100]).
        """

        super().__init__(DcMotor.State(speed))

        self.enable_pin = enable_pin
        self.in_1_pin = in_1_pin
        self.in_2_pin = in_2_pin

        gpio.setup(self.enable_pin, gpio.OUT)
        gpio.setup(self.in_1_pin, gpio.OUT)
        gpio.setup(self.in_2_pin, gpio.OUT)

        self.pwm_enable = gpio.PWM(self.enable_pin, 1000)
