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

        # zero speed does not rotate
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


class Servo(Component):
    """
    Servo.
    """

    class State(Component.State):
        """
        Servo state.
        """

        def __init__(
                self,
                degrees: float
        ):
            """
            Initialize the state.

            :param degrees: Degrees of rotation.
            """

            self.degrees = degrees

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Servo.State):
                raise ValueError(f'Expected a {Servo.State}')

            return self.degrees == other.degrees

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Degrees:  {self.degrees}'

    def set_state(
            self,
            state: 'Component.State'
    ):
        """
        Set the state of the servo.

        :param state: State.
        """

        if not isinstance(state, Servo.State):
            raise ValueError(f'Expected a {Servo.State}')

        super().set_state(state)

        state: Servo.State

        if state.degrees < self.min_degree or state.degrees > self.max_degree:
            raise ValueError(f'Degree must be in [{self.min_degree},{self.max_degree}].')

        self.pwm_signal.ChangeDutyCycle(self.get_duty_cycle())

    def set_degrees(
            self,
            degrees: float
    ):
        """
        Set degrees of rotation.

        :param degrees: Degrees.
        """

        self.set_state(Servo.State(degrees))

    def get_degrees(
            self
    ) -> float:
        """
        Get degrees of rotation.

        :return: Degrees.
        """

        self.state: Servo.State

        return self.state.degrees

    def get_duty_cycle(
            self
    ) -> float:
        """
        Get PWM duty cycle for the current state.
        :return: Duty cycle in [0%,100%].
        """

        self.state: Servo.State

        # get fraction into degree range
        degree_range = self.max_degree - self.min_degree
        range_fraction = (self.state.degrees - self.min_degree) / degree_range

        # get ms with pwm set to high
        pwm_high_range_ms = self.max_pwm_high_ms - self.min_pwm_high_ms
        duty_cycle_high_ms = self.min_pwm_high_ms + range_fraction * pwm_high_range_ms + self.pwm_high_offset_ms

        # get duty cycle percent
        duty_cycle_percent = 100.0 * duty_cycle_high_ms / self.pwm_tick_ms

        return duty_cycle_percent

    def start(
            self
    ):
        """
        Start the servo at its current rotation.
        """

        self.state: Servo.State

        self.pwm_signal.start(self.get_duty_cycle())

    def stop(
            self
    ):
        """
        Stop the servo.
        """

        self.pwm_signal.stop()

    def __init__(
            self,
            signal_pin: int,
            min_pwm_high_ms: float,
            max_pwm_high_ms: float,
            pwm_high_offset_ms: float,
            min_degree: float,
            max_degree: float,
            degrees: float
    ):
        """
        Initialize the servo.

        :param signal_pin: Servo signal pin on which PWM outputs.
        :param min_pwm_high_ms: Servo's minimum PWM high time (ms).
        :param max_pwm_high_ms: Servo's maximum PWM high time (ms).
        :param pwm_high_offset_ms: Offset (ms).
        :param min_degree: Servo's minimum degree angle.
        :param max_degree: Servo's maximum degree angle.
        :param degrees: Initial degree angle.
        """

        super().__init__(Servo.State(degrees))

        self.signal_pin = signal_pin
        self.min_pwm_high_ms = min_pwm_high_ms
        self.max_pwm_high_ms = max_pwm_high_ms
        self.pwm_high_offset_ms = pwm_high_offset_ms
        self.min_degree = min_degree
        self.max_degree = max_degree

        self.pwm_hz = 50
        self.pwm_tick_ms = 1000 / self.pwm_hz
        if self.max_pwm_high_ms > self.pwm_tick_ms:
            raise ValueError(f'The value of max_pwm_high_ms ({self.max_pwm_high_ms}) must be less than the PWM tick duration ({self.pwm_tick_ms}).')

        gpio.setup(self.signal_pin, gpio.OUT)
        gpio.output(self.signal_pin, gpio.LOW)
        self.pwm_signal = gpio.PWM(self.signal_pin, self.pwm_hz)
