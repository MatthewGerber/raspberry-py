import logging
import time
from abc import ABC, abstractmethod
from datetime import timedelta, datetime
from typing import Optional, Callable

import RPi.GPIO as gpio
import numpy as np

from raspberry_py.gpio import Component, CkPin
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW


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


class DcMotorDriverL293D(DcMotorDriver):
    """
    Motor driver via L293D IC and software pulse-wave modulation (PWM). This is a direct driver, in that the PWM outputs
    go directly to the motor to provide driving current. This is appropriate when the PWM voltage alone is sufficient
    for the motor (e.g., a small 5v motor).
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
    Motor driver via PCA9685PW IC hardware pulse-wave modulator (PWM). This is a direct driver, in that the PWM outputs
    go directly to the motor to provide driving current.  This is appropriate when the PWM voltage alone is sufficient
    for the motor (e.g., a small 5v motor).
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
            duty = int((abs(new_state.speed) / 100.0) * 4095)
        else:
            duty = 0

        self.pca9685pw.set_channel_pwm_on_off(drive_channel, 0, duty)
        self.pca9685pw.set_channel_pwm_on_off(zero_channel, 0, 0)

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            motor_channel_1: int,
            motor_channel_2: int,
            reverse: bool = False
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


class DcMotorDriverIndirectPCA9685PW(DcMotorDriver):
    """
    Motor driver via PCA9685PW IC hardware pulse-wave modulator (PWM). This is an indirect driver, in that the PWM
    outputs go to an intermediate DC motor controller that supplies driving current to the motor. This is appropriate
    when the PWM voltage alone is insufficient for the motor (e.g., a larger 12v or 24v motor). In this case, the
    intermediate motor controller has a separate larger power supply, and the PWM serves as the controlling signal for
    the motor controller's voltage regulator.
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
            direction = gpio.HIGH
        else:
            direction = gpio.LOW

        if self.reverse:
            direction = gpio.LOW if direction == gpio.HIGH else gpio.HIGH

        gpio.output(self.direction_pin, direction)

        if new_state.on:
            duty = int((abs(new_state.speed) / 100.0) * 4095)
        else:
            duty = 0

        self.pca9685pw.set_channel_pwm_on_off(self.drive_channel, 0, duty)

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            pwm_channel: int,
            direction_pin: CkPin,
            reverse: bool = False
    ):
        """
        Initialize the driver.

        :param pca9685pw: IC.
        :param pwm_channel: PWM channel to drive.  
        :param direction_pin: Direction pin, which outputs to the controller's direction input.
        :param reverse: Whether to reverse speed upon output.
        """

        self.pca9685pw = pca9685pw
        self.drive_channel = pwm_channel
        self.direction_pin = direction_pin
        self.reverse = reverse

        gpio.setup(self.direction_pin, gpio.OUT)


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

        constrained_speed = min(self.max_speed, max(state.speed, self.min_speed))
        if constrained_speed != state.speed:
            logging.warning(
                f'Requested motor speed ({state.speed}) is out of bounds [{self.min_speed},{self.max_speed}]. '
                f'Constraining to be in bounds.'
            )
            state.speed = constrained_speed

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
            speed: int,
            min_speed: int = -100,
            max_speed: int = 100
    ):
        """
        Initialize the motor.

        :param driver: Driver.
        :param speed: Initial speed in [-100,+100].
        :param min_speed: Minimum speed in [-100,+100].
        :param max_speed: Maximum speed in [-100,+100].
        """

        super().__init__(DcMotor.State(on=False, speed=speed))

        self.driver = driver

        self.min_speed = min_speed
        self.max_speed = max_speed


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

    def __init__(
            self,
            min_degree: float,
            max_degree: float
    ):
        """
        Initialize the driver.

        :param min_degree: Minimum degree.
        :param max_degree: Maximum degree.
        """

        if min_degree >= max_degree:
            raise ValueError('Minimum degree must be less than maximum degree.')

        self.min_degree = min_degree
        self.max_degree = max_degree

        self.degree_range = self.max_degree - self.min_degree


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

        super().__init__(
            min_degree=min_degree,
            max_degree=max_degree
        )

        self.signal_pin = signal_pin
        self.min_pwm_high_ms = min_pwm_high_ms
        self.max_pwm_high_ms = max_pwm_high_ms
        self.pwm_high_offset_ms = pwm_high_offset_ms

        self.pwm_hz = 50
        self.pwm_tick_ms = 1000 / self.pwm_hz
        if self.max_pwm_high_ms > self.pwm_tick_ms:
            raise ValueError(
                f'The value of max_pwm_high_ms ({self.max_pwm_high_ms}) must be less than the PWM tick duration '
                f'({self.pwm_tick_ms}).'
            )

        gpio.setup(self.signal_pin, gpio.OUT)
        gpio.output(self.signal_pin, gpio.LOW)
        self.pwm_signal = gpio.PWM(self.signal_pin, self.pwm_hz)


class ServoDriverPCA9685PW(ServoDriver):
    """
    Servo driver via PCA9685PW IC (hardware pulse-wave modulator). This is intended for use with servos with angular
    ranges that correspond to ranges in the PWM pulse width. For example, see the SG90 servo (sg90_servo.pdf).
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

            # constrain degrees to the specified range
            degrees_to_set = max(min(new_state.degrees + self.correction_degrees, self.max_degree), self.min_degree)

            # convert to percent of range and reverse if specified
            percent_of_range = (degrees_to_set - self.min_degree) / self.degree_range
            if self.reverse:
                percent_of_range = 1.0 - percent_of_range

            # calculate pulse width and convert to discrete tick
            pulse_width_ms = self.min_degree_pulse_width_ms + percent_of_range * self.pulse_width_range
            off_tick = self.pca9685pw.get_tick(pulse_width_ms)
        else:
            off_tick = 0

        self.pca9685pw.set_channel_pwm_on_off(self.servo_channel, 0, off_tick)

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            servo_channel: int,
            min_degree: float,
            min_degree_pulse_width_ms: float,
            max_degree: float,
            max_degree_pulse_width_ms: float,
            reverse: bool = False,
            correction_degrees: float = 0.0
    ):
        """
        Initialize the driver.

        :param pca9685pw: IC.
        :param servo_channel: Channel of PCA9685PW to which the servo is connected.
        :param min_degree: Minimum degree of the servo.
        :param min_degree_pulse_width_ms: Pulse width (ms) corresponding to the minimum degree.
        :param max_degree: Maximum degree of the servo.
        :param max_degree_pulse_width_ms: Pulse width (ms) corresponding to the maximum degree.
        :param reverse: Whether to reverse the degrees upon output.
        :param correction_degrees: Correction degrees to be added to any requested degrees to account for assembly
        errors (e.g., a servo not being mounted perfectly).
        """

        if min_degree_pulse_width_ms >= max_degree_pulse_width_ms:
            raise ValueError('Minimum-degree pulse width must be less than maximum-degree pulse width.')

        super().__init__(
            min_degree=min_degree,
            max_degree=max_degree
        )

        self.pca9685pw = pca9685pw
        self.servo_channel = servo_channel
        self.min_degree_pulse_width_ms = min_degree_pulse_width_ms
        self.max_degree_pulse_width_ms = max_degree_pulse_width_ms
        self.reverse = reverse
        self.correction_degrees = correction_degrees

        self.pulse_width_range = self.max_degree_pulse_width_ms - self.min_degree_pulse_width_ms


class Sg90DriverPCA9685PW(ServoDriverPCA9685PW):
    """
    A SG-90 specific servo driver based on the PCA9685PW PWM chip. See manuals/sg90_servo.pdf for details about the
    servo.
    """

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            servo_channel: int,
            reverse: bool = False,
            correction_degrees: float = 0.0
    ):
        """
        Initialize the driver.

        :param pca9685pw: IC.
        :param servo_channel: Channel of PCA9685PW to which the servo is connected.
        :param reverse: Whether to reverse the degrees upon output.
        :param correction_degrees: Correction degrees to be added to any requested degrees to account for assembly
        errors (e.g., a servo not being mounted perfectly).
        """

        super().__init__(
            pca9685pw=pca9685pw,
            servo_channel=servo_channel,
            reverse=reverse,
            min_degree=0.0,
            min_degree_pulse_width_ms=0.5,
            max_degree=180.0,
            max_degree_pulse_width_ms=2.5,
            correction_degrees=correction_degrees
        )


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
            state: Component.State
    ):
        """
        Set the state of the servo.

        :param state: State.
        """

        if not isinstance(state, Servo.State):
            raise ValueError(f'Expected a {Servo.State}')

        constrained_degrees = min(self.max_degree, max(state.degrees, self.min_degree))
        if constrained_degrees != state.degrees:
            logging.warning(
                f'Requested servo degrees ({state.degrees}) is out of bounds [{self.min_degree},{self.max_degree}]. '
                f'Constraining to be in bounds.'
            )
            state.degrees = constrained_degrees

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
            min_degree: float,
            max_degree: float
    ):
        """
        Initialize the servo.

        :param driver: Driver.
        :param degrees: Initial degree angle.
        :param min_degree: Minimum degree. This minimum differs from the driver's minimum in that the former is used to
        constrain the movement of the servo, whereas the latter is used to establish the range of the servo.
        :param max_degree: Maximum degree. This maximum differs from the driver's maximum in that the former is used to
        constrain the movement of the servo, whereas the latter is used to establish the range of the servo.
        """

        super().__init__(Servo.State(on=False, degrees=degrees))

        self.driver = driver
        self.degrees = degrees
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
            state: Component.State
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        if not isinstance(state, Stepper.State):
            raise ValueError(f'Expected a {Stepper.State}')

        state: Stepper.State
        self.state: Stepper.State

        initial_step = self.state.step
        curr_time = datetime.now()

        # get number of steps to move and how long to take for each step
        num_steps = state.step - initial_step
        if num_steps == 0:
            print(f'Stepper is already at step {state.step}. Nothing to do.')
            return

        delay_seconds_per_step = state.time_to_step.total_seconds() / abs(num_steps)

        # execute steps in the direction indicated
        direction = np.sign(num_steps)
        limited = False
        for next_step in range(initial_step + direction, state.step + direction, direction):

            # check for limiting. provide the anticipated next state.
            next_state = Stepper.State(next_step, timedelta(seconds=delay_seconds_per_step))
            if self.limiter is not None and self.limiter(self.state, next_state):
                print(f'Stepper has been limited. Refusing to set state to {next_state} or proceed beyond.')
                limited = True
                break

            # drive to next step
            self.current_driver_pin_idx = (self.current_driver_pin_idx + direction) % len(self.driver_pins)
            self.drive()

            # update state. we do this here (rather than at the end of this function) so that event listeners can react
            # in real time as the stepper moves. update the anticipated time to step with the actual.
            new_time = datetime.now()
            next_state.time_to_step = new_time - curr_time
            super().set_state(next_state)
            curr_time = new_time

            # sleep for a bit
            time.sleep(delay_seconds_per_step)

        if not limited and self.state.step != state.step:
            raise ValueError(f'Expected stepper state ({self.state.step}) to be {state.step}.')

    def step(
            self,
            steps: int,
            time_to_step: timedelta
    ):
        """
        Step the motor a number of steps.

        :param steps:  Number of steps.
        :param time_to_step: Amount of time to take.
        """

        self.state: Stepper.State

        self.set_state(Stepper.State(self.state.step + steps, time_to_step))

    def step_degrees(
            self,
            degrees: float,
            time_to_step: timedelta
    ):
        """
        Step the motor a number of degrees.

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

    def get_step(
            self
    ) -> int:
        """
        Get current step of the output shaft.

        :return: Step.
        """

        self.state: Stepper.State

        return self.state.step

    def __init__(
            self,
            poles: int,
            output_rotor_ratio: float,
            driver_pin_1: int,
            driver_pin_2: int,
            driver_pin_3: int,
            driver_pin_4: int,
            limiter: Optional[Callable[['Stepper.State', 'Stepper.State'], bool]] = None
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
        :param limiter: Limiter function, which takes the current stepper state and the next stepper state and returns a
        bool indicating whether the stepper has reached its limit and should stop.
        """

        super().__init__(Stepper.State(0, timedelta(seconds=0)))

        self.poles = poles
        self.output_rotor_ratio = output_rotor_ratio
        self.driver_pin_1 = driver_pin_1
        self.driver_pin_2 = driver_pin_2
        self.driver_pin_3 = driver_pin_3
        self.driver_pin_4 = driver_pin_4
        self.limiter = limiter

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
