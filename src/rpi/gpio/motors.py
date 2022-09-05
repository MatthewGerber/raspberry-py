import time
from datetime import timedelta

import RPi.GPIO as gpio
import numpy as np

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
                on: bool,
                speed: int
        ):
            """
            Initialize the state.

            :param on: Whether the motor is on.
            :param speed: Speed (if on).
            """

            self.on = on
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

            return self.on == other.on and self.speed == other.speed

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'On:  {self.on}, Speed:  {self.speed}'

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

        self.state: DcMotor.State
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

        if state.on:
            pwm_duty_cycle = abs(state.speed)
            if self.state.on:
                self.pwm_enable.ChangeDutyCycle(pwm_duty_cycle)
            else:
                self.pwm_enable.start(pwm_duty_cycle)
        else:
            self.pwm_enable.stop()

        super().set_state(state)

    def start(
            self
    ):
        """
        Start the motor at the current speed.
        """

        self.state: DcMotor.State
        self.set_state(DcMotor.State(on=True, speed=self.state.speed))

    def stop(
            self
    ):
        """
        Stop the motor.
        """

        self.state: DcMotor.State
        self.set_state(DcMotor.State(on=False, speed=self.state.speed))

    def set_speed(
            self,
            speed: int
    ):
        """
        Set the motor's speed.

        :param speed: Speed (in [-100,+100]).
        """

        self.state: DcMotor.State
        self.set_state(DcMotor.State(on=self.state.on, speed=speed))

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

        super().__init__(DcMotor.State(on=False, speed=speed))

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


class Stepper(Component):
    """
    Stepper motor.
    """

    class State(Component.State):
        """
        Stepper motor state.
        """

        def __init__(
                self,
                step: int,
                time_to_step: timedelta
        ):
            """
            Initialize the state.

            :param step: Step to position at.
            :param time_to_step: Amount of time to take to position at step.
            """

            self.step = step
            self.time_to_step = time_to_step

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Stepper.State):
                raise ValueError(f'Expected a {Stepper.State}')

            return self.step == other.step

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'Step:  {self.step}'

    def set_state(
            self,
            state: 'Component.State'
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, Stepper.State):
            raise ValueError(f'Expected a {Stepper.State}')

        state: Stepper.State
        self.state: Stepper.State

        # get number of steps to move and how long to take for each step
        num_steps = state.step - self.state.step
        delay_seconds_per_step = state.time_to_step.total_seconds() / abs(num_steps)

        # execute steps
        direction = np.sign(num_steps)
        for _ in range(abs(num_steps)):
            self.current_driver_pin_idx = (self.current_driver_pin_idx + direction) % len(self.driver_pins)
            self.drive()
            time.sleep(delay_seconds_per_step)

        # trigger events now that steps are complete
        super().set_state(state)

    def step(
            self,
            degrees: float,
            time_to_step: timedelta
    ):
        """
        Step the motor.

        :param degrees:  Number of degrees.
        :param time_to_step: Amount of time to take.
        """

        self.state: Stepper.State

        self.set_state(Stepper.State(self.state.step + round(degrees * self.steps_per_degree), time_to_step))

    def start(
            self
    ):
        """
        Start the motor.
        """

        self.drive()

    def stop(
            self
    ):
        """
        Stop the motor.
        """

        for driver_pin in self.driver_pins:
            gpio.output(driver_pin, gpio.LOW)

    def drive(
            self
    ):
        """
        Drive the motor with the currently selected driver pin.
        """

        for i, driver_pin in enumerate(self.driver_pins):
            gpio.output(driver_pin, gpio.HIGH if i == self.current_driver_pin_idx else gpio.LOW)

    def get_degrees(
            self
    ) -> float:
        """
        Get current degree rotation of the output shaft.

        :return: Degrees.
        """

        self.state: Stepper.State

        return (self.state.step / self.steps_per_degree) % 360.0

    def __init__(
            self,
            poles: int,
            output_rotor_ratio: float,
            driver_pin_1: int,
            driver_pin_2: int,
            driver_pin_3: int,
            driver_pin_4: int
    ):
        """
        Initialize the motor.

        :param poles: Number of poles in the stepper.
        :param output_rotor_ratio: Rotor/output ratio (e.g., if the output shaft rotates one time per 100 rotations of
        the internal rotor, then this value would be 1/100).
        :param driver_pin_1: Driver GPIO pin 1.
        :param driver_pin_2: Driver GPIO pin 2.
        :param driver_pin_3: Driver GPIO pin 3.
        :param driver_pin_4: Driver GPIO pin 4.
        """

        super().__init__(Stepper.State(0, timedelta(seconds=0)))

        self.poles = poles
        self.output_rotor_ratio = output_rotor_ratio
        self.driver_pin_1 = driver_pin_1
        self.driver_pin_2 = driver_pin_2
        self.driver_pin_3 = driver_pin_3
        self.driver_pin_4 = driver_pin_4

        self.steps_per_degree = (poles / output_rotor_ratio) / 360.0

        self.driver_pins = [
            self.driver_pin_1,
            self.driver_pin_2,
            self.driver_pin_3,
            self.driver_pin_4
        ]

        for driver_pin in self.driver_pins:
            gpio.setup(driver_pin, gpio.OUT)
            gpio.output(driver_pin, gpio.LOW)

        self.current_driver_pin_idx = 0
