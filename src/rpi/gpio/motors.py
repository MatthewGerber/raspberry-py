import logging
import time
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional

import RPi.GPIO as gpio
import numpy as np

from rpi.gpio import Component
from rpi.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW


class DcMotorDriver(ABC):
    """
    DC motor driver.
    """

    @abstractmethod
    def change_state(
            self,
            previous_state: 'DcMotor.State',
            new_state: 'DcMotor.State'
    ):
        """
        Change state.

        :param previous_state: Previous state.
        :param new_state: New state.
        """
        pass


class DcMotorDriverL293D(DcMotorDriver):
    """
    Motor driver via L293D IC and software pulse-wave modulation.
    """

    def change_state(
            self,
            previous_state: 'DcMotor.State',
            new_state: 'DcMotor.State'
    ):
        """
        Change state.

        :param previous_state: Previous state.
        :param new_state: New state.
        """

        # negative speed rotates one direction
        if new_state.speed < 0:
            gpio.output(self.in_1_pin, gpio.HIGH)
            gpio.output(self.in_2_pin, gpio.LOW)

        # positive speed rotates in the other direction
        elif new_state.speed > 0:
            gpio.output(self.in_1_pin, gpio.LOW)
            gpio.output(self.in_2_pin, gpio.HIGH)

        # zero speed does not rotate
        else:
            gpio.output(self.in_1_pin, gpio.LOW)
            gpio.output(self.in_2_pin, gpio.LOW)

        if new_state.on:
            pwm_duty_cycle = abs(new_state.speed)
            if previous_state.on:
                self.pwm_enable.ChangeDutyCycle(pwm_duty_cycle)
            else:
                self.pwm_enable.start(pwm_duty_cycle)
        else:
            self.pwm_enable.stop()

    def __init__(
            self,
            enable_pin: int,
            in_1_pin: int,
            in_2_pin: int
    ):
        """
        Initialize the driver.

        :param enable_pin: GPIO pin connected to the enable pin of the L293D IC.
        :param in_1_pin: GPIO pin connected to the in-1 pin of the L293D IC.
        :param in_2_pin: GPIO pin connected to the in-2 pin of the L293D IC.
        """

        self.enable_pin = enable_pin
        self.in_1_pin = in_1_pin
        self.in_2_pin = in_2_pin

        gpio.setup(self.enable_pin, gpio.OUT)
        gpio.setup(self.in_1_pin, gpio.OUT)
        gpio.setup(self.in_2_pin, gpio.OUT)

        self.pwm_enable = gpio.PWM(self.enable_pin, 1000)


class DcMotorDriverPCA9685PW(DcMotorDriver):
    """
    Motor driver via PCA9685PW IC (hardware pulse-wave modulator).
    """

    def change_state(
            self,
            previous_state: 'DcMotor.State',
            new_state: 'DcMotor.State'
    ):
        """
        Change state.

        :param previous_state: Previous state.
        :param new_state: New state.
        """

        if new_state.speed >= 0:
            drive_channel, zero_channel = (self.motor_channel_1, self.motor_channel_2)
        else:
            drive_channel, zero_channel = (self.motor_channel_2, self.motor_channel_1)

        if self.reverse:
            drive_channel, zero_channel = zero_channel, drive_channel

        if new_state.on:
            speed_frac = abs(new_state.speed) / 100.0
            duty = int(speed_frac * 4095)
        else:
            duty = 0

        self.pca9685pw.set_channel_pwm_on_off(drive_channel, 0, duty)
        self.pca9685pw.set_channel_pwm_on_off(zero_channel, 0, 0)

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            motor_channel_1: int,
            motor_channel_2: int,
            reverse: bool
    ):
        """
        Initialize the driver.

        :param pca9685pw: IC.
        :param motor_channel_1: Channel of PCA9685PW to which the motor lead 1 is connected.
        :param motor_channel_2: Channel of PCA9685PW to which the motor lead 2 is connected.
        :param reverse: Whether to reverse speed upon output.
        """

        self.pca9685pw = pca9685pw
        self.motor_channel_1 = motor_channel_1
        self.motor_channel_2 = motor_channel_2
        self.reverse = reverse


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

        self.driver.change_state(self.state, state)

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

        :param speed: Speed in [-100,+100].
        """

        self.state: DcMotor.State
        self.set_state(DcMotor.State(on=self.state.on, speed=speed))

    def get_speed(
            self
    ) -> int:
        """
        Get the current speed.

        :return: Current speed in [-100,+100].
        """

        self.state: DcMotor.State

        return self.state.speed

    def __init__(
            self,
            driver: DcMotorDriver,
            speed: int
    ):
        """
        Initialize the motor.

        :param driver: Driver.
        :param speed: Initial speed in [-100,+100].
        """

        super().__init__(DcMotor.State(on=False, speed=speed))

        self.driver = driver


class ServoDriver(ABC):
    """
    Servo driver.
    """

    @abstractmethod
    def change_state(
            self,
            previous_state: 'Servo.State',
            new_state: 'Servo.State'
    ):
        """
        Change state.

        :param previous_state: Previous state.
        :param new_state: New state.
        """


class ServoDriverSoftwarePWM(ServoDriver):
    """
    Software PWM servo driver.
    """

    def change_state(
            self,
            previous_state: 'Servo.State',
            new_state: 'Servo.State'
    ):
        """
        Change state.

        :param previous_state: Previous state.
        :param new_state: New state.
        """

        if new_state.on:
            pwm_duty_cycle = self.get_duty_cycle(new_state.degrees)
            if previous_state.on:
                self.pwm_signal.ChangeDutyCycle(pwm_duty_cycle)
            else:
                self.pwm_signal.start(pwm_duty_cycle)
        else:
            self.pwm_signal.stop()

    def get_duty_cycle(
            self,
            degrees: float
    ) -> float:
        """
        Get PWM duty cycle for the current state.

        :param degrees: Degrees.
        :return: Duty cycle in [0%,100%].
        """

        # get fraction into degree range
        degree_range = self.max_degree - self.min_degree
        range_fraction = (degrees - self.min_degree) / degree_range

        # get ms with pwm set to high
        pwm_high_range_ms = self.max_pwm_high_ms - self.min_pwm_high_ms
        duty_cycle_high_ms = self.min_pwm_high_ms + range_fraction * pwm_high_range_ms + self.pwm_high_offset_ms

        # get duty cycle percent
        duty_cycle_percent = 100.0 * duty_cycle_high_ms / self.pwm_tick_ms

        return duty_cycle_percent

    def __init__(
            self,
            signal_pin: int,
            min_pwm_high_ms: float,
            max_pwm_high_ms: float,
            pwm_high_offset_ms: float,
            min_degree: float,
            max_degree: float
    ):
        """
        Initialize the driver.

        :param signal_pin: Servo signal pin on which PWM outputs.
        :param min_pwm_high_ms: Servo's minimum PWM high time (ms).
        :param max_pwm_high_ms: Servo's maximum PWM high time (ms).
        :param pwm_high_offset_ms: Offset (ms).
        :param min_degree: Servo's minimum degree angle.
        :param max_degree: Servo's maximum degree angle.
        """

        self.signal_pin = signal_pin
        self.min_pwm_high_ms = min_pwm_high_ms
        self.max_pwm_high_ms = max_pwm_high_ms
        self.pwm_high_offset_ms = pwm_high_offset_ms
        self.min_degree = min_degree
        self.max_degree = max_degree

        self.pwm_hz = 50
        self.pwm_tick_ms = 1000 / self.pwm_hz
        if self.max_pwm_high_ms > self.pwm_tick_ms:
            raise ValueError(
                f'The value of max_pwm_high_ms ({self.max_pwm_high_ms}) must be less than the PWM tick duration ({self.pwm_tick_ms}).'
            )

        gpio.setup(self.signal_pin, gpio.OUT)
        gpio.output(self.signal_pin, gpio.LOW)
        self.pwm_signal = gpio.PWM(self.signal_pin, self.pwm_hz)


class ServoDriverPCA9685PW(ServoDriver):
    """
    Servo driver via PCA9685PW IC (hardware pulse-wave modulator).
    """

    def change_state(
            self,
            previous_state: 'Servo.State',
            new_state: 'Servo.State'
    ):
        """
        Change state.

        :param previous_state: Previous state.
        :param new_state: New state.
        """

        if new_state.on:

            if self.reverse:
                pulse = 500 + int((new_state.degrees + self.correction_degrees) / 0.09)
            else:
                pulse = 2500 - int((new_state.degrees + self.correction_degrees) / 0.09)

            duty = int(pulse * 4096 / 20000)  # PWM frequency is 50HZ, the period is 20000us

        else:
            duty = 0

        self.pca9685pw.set_channel_pwm_on_off(self.servo_channel, 0, duty)

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            servo_channel: int,
            reverse: bool,
            correction_degrees: float
    ):
        """
        Initialize the driver.

        :param pca9685pw: IC.
        :param servo_channel: Channel of PCA9685PW to which the servo is connected.
        :param reverse: Whether to reverse the degrees upon output.
        :param correction_degrees: Correction degrees to be added to any requested degrees to account for assembly
        errors (e.g., a servo not being mounted perfectly).
        """

        self.pca9685pw = pca9685pw
        self.servo_channel = servo_channel
        self.reverse = reverse
        self.correction_degrees = correction_degrees


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
                on: bool,
                degrees: float
        ):
            """
            Initialize the state.

            :param on: Whether servo is on.
            :param degrees: Degrees of rotation.
            """

            self.on = on
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

            return self.on == other.on and self.degrees == other.degrees

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'On:  {self.on}, Degrees:  {self.degrees}'

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

        state: Servo.State

        constrained_degrees = min(self.max_degree, max(state.degrees, self.min_degree))
        if constrained_degrees != state.degrees:
            logging.warning(f'Requested servo degrees ({state.degrees}) is out of bounds [{self.min_degree},{self.max_degree}]. Constraining to be in bounds.')
            state.degrees = constrained_degrees

        self.state: DcMotor.State
        state: DcMotor.State

        self.driver.change_state(self.state, state)

        super().set_state(state)

    def set_degrees(
            self,
            degrees: float,
            interval: Optional[timedelta] = None
    ):
        """
        Set degrees of rotation.

        :param degrees: Degrees.
        :param interval: Interval of time to take when changing degrees from the current to the specified value (None to
        change as quickly as possible).
        """

        self.state: Servo.State

        if interval is not None:
            start_degrees = self.get_degrees()
            num_steps = int(abs(degrees - start_degrees) * 1.0)
            seconds_per_step = interval.total_seconds() / num_steps
            degrees_per_step = (degrees - start_degrees) / num_steps
            for step in range(num_steps):
                step_degrees = start_degrees + step * degrees_per_step
                self.set_state(Servo.State(on=self.state.on, degrees=step_degrees))
                time.sleep(seconds_per_step)

        self.set_state(Servo.State(on=self.state.on, degrees=degrees))

    def get_degrees(
            self
    ) -> float:
        """
        Get degrees of rotation.

        :return: Degrees.
        """

        self.state: Servo.State

        return self.state.degrees

    def start(
            self
    ):
        """
        Start the servo at its current rotation.
        """

        self.state: Servo.State
        self.set_state(Servo.State(on=True, degrees=self.state.degrees))

    def stop(
            self
    ):
        """
        Stop the servo.
        """

        self.state: Servo.State
        self.set_state(Servo.State(on=False, degrees=self.state.degrees))

    def __init__(
            self,
            driver: ServoDriver,
            degrees: float,
            min_degree: float = 0.0,
            max_degree: float = 180.0
    ):
        """
        Initialize the servo.

        :param driver: Driver.
        :param degrees: Initial degree angle.
        :param min_degree: Minimum allowable degree.
        :param max_degree: Maximum allowable degree.
        """

        if min_degree > max_degree:
            raise ValueError('Minimum degree must not be greater than maximum degree.')

        super().__init__(Servo.State(on=False, degrees=degrees))

        self.driver = driver
        self.min_degree = min_degree
        self.max_degree = max_degree


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
