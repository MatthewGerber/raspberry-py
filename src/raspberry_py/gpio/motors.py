import logging
import time
from abc import ABC, abstractmethod
from datetime import timedelta
from enum import IntEnum
from typing import Optional, Callable, Any, Tuple, List, Union

import RPi.GPIO as gpio
import numpy as np
from raspberry_py.gpio import Component, CkPin
from raspberry_py.gpio.communication import LockingSerial
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.rest.application import RpyFlask
from raspberry_py.utils import get_float


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


class DcMotorDriverIndirectArduino(DcMotorDriver):
    """
    Motor driver via serial connection to an Arduino board, which controls the DC motor. This is an indirect driver, in
    that the outputs go first to the Arduino. How the DC motor is controlled from that point is unspecified. The
    Arduino might directly control the DC motor with PWM, or it might control it indirectly via a DC motor controller
    board.
    """

    class Command(IntEnum):
        """
        Commands that can be sent to the Arduino.
        """

        INIT = 1
        SET_SPEED = 5

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

        new_speed = None
        promise_ms = None

        if not previous_state.on and new_state.on:
            self.serial.write_then_read(
                DcMotorDriverIndirectArduino.Command.INIT.to_bytes(1) +
                self.identifier.to_bytes(1) +
                self.arduino_direction_pin.to_bytes(1) +
                self.arduino_pwm_pin.to_bytes(1),
                True,
                0,
                False
            )
        elif previous_state.on and not new_state.on:
            new_speed = 0
            promise_ms = 0
        else:
            new_speed = -new_state.speed if self.reverse else new_state.speed
            promise_ms = self.next_set_speed_promise_ms if self.send_promise else 0

        if new_speed is not None and promise_ms is not None:
            self.serial.write_then_read(
                DcMotorDriverIndirectArduino.Command.SET_SPEED.to_bytes(1) +
                self.identifier.to_bytes(1) +
                abs(new_speed).to_bytes(2) +
                (new_speed > 0).to_bytes(1) +
                promise_ms.to_bytes(2),
                True,
                0,
                False
            )

    def __init__(
            self,
            identifier: int,
            serial: LockingSerial,
            arduino_direction_pin: int,
            arduino_pwm_pin: int,
            next_set_speed_promise_ms: int,
            reverse: bool = False
    ):
        """
        Initialize the driver.

        :param identifier: Identifier.
        :param serial: Serial connection to the Arduino.
        :param arduino_direction_pin: Direction pin on the Arduino.
        :param arduino_pwm_pin: PWM pin on the Arduino.
        :param next_set_speed_promise_ms: Milliseconds within which the next speed will be set.
        :param reverse: Whether to reverse speed upon output.
        """

        self.identifier = identifier
        self.serial = serial
        self.arduino_direction_pin = arduino_direction_pin
        self.arduino_pwm_pin = arduino_pwm_pin
        self.next_set_speed_promise_ms = next_set_speed_promise_ms
        self.reverse = reverse

        self.send_promise = False


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

        constrained_speed = self.constrain_speed(state.speed)
        if constrained_speed != state.speed:
            logging.warning(
                f'Requested motor speed ({state.speed}) is out of bounds [{self.min_speed},{self.max_speed}]. '
                f'Constraining to be in bounds.'
            )
            state.speed = constrained_speed

        self.driver.change_state(self.state, state)

        super().set_state(state)

    def constrain_speed(
            self,
            speed: int
    ) -> int:
        """
        Constrain speed to be in the motor's range.

        :param speed: Speed.
        :return: Constrained speed.
        """

        return min(self.max_speed, max(self.min_speed, speed))

    def start(
            self
    ):
        """
        Start the motor at the current speed.
        """

        state: DcMotor.State = self.state
        self.set_state(DcMotor.State(on=True, speed=state.speed))

    def stop(
            self
    ):
        """
        Stop the motor.
        """

        state: DcMotor.State = self.state
        self.set_state(DcMotor.State(on=False, speed=state.speed))

    def set_speed(
            self,
            speed: int
    ):
        """
        Set the motor's speed.

        :param speed: Speed in [-100,+100].
        """

        state: DcMotor.State = self.state
        self.set_state(DcMotor.State(on=state.on, speed=speed))

    def get_speed(
            self
    ) -> int:
        """
        Get the current speed.

        :return: Current speed in [-100,+100].
        """

        state: DcMotor.State = self.state

        return state.speed

    def get_ui_elements(
            self
    ):
        """
        Get UI elements for the current component.

        :return: List of 2-tuples of (1) element key and (2) element content.
        """

        curr_state: DcMotor.State = self.state

        return [
            RpyFlask.get_switch(self.id, self.start, self.stop, None, curr_state.on),
            RpyFlask.get_range(self.id, self.min_speed, self.max_speed, 1, self.get_speed(), False,False, [], [], [], False, self.set_speed, None, False)
        ]

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
    ranges that correspond to ranges in the PWM pulse width. For example, see the SG90 servo
    (manuals/datasheets/sg90_servo.pdf).
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

        if self.output_disable_pin is not None:
            gpio.output(self.output_disable_pin, gpio.LOW if new_state.enabled else gpio.HIGH)

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
            output_disable_pin: Optional[CkPin],
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
        :param output_disable_pin: Output disable GPIO pin, or pass None to always enable PWM output.
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
        self.output_disable_pin = output_disable_pin
        self.servo_channel = servo_channel
        self.min_degree_pulse_width_ms = min_degree_pulse_width_ms
        self.max_degree_pulse_width_ms = max_degree_pulse_width_ms
        self.reverse = reverse
        self.correction_degrees = correction_degrees

        self.pulse_width_range = self.max_degree_pulse_width_ms - self.min_degree_pulse_width_ms

        if self.output_disable_pin is not None:
            gpio.setup(self.output_disable_pin, gpio.OUT)


class Sg90DriverPCA9685PW(ServoDriverPCA9685PW):
    """
    A SG-90 specific servo driver based on the PCA9685PW PWM chip. See manuals/datasheets/sg90_servo.pdf for details
    about the servo.
    """

    def __init__(
            self,
            pca9685pw: PulseWaveModulatorPCA9685PW,
            output_disable_pin: Optional[CkPin],
            servo_channel: int,
            reverse: bool = False,
            correction_degrees: float = 0.0
    ):
        """
        Initialize the driver.

        :param pca9685pw: IC.
        :param output_disable_pin: Output disable GPIO pin, or pass None to always enable PWM output.
        :param servo_channel: Channel of PCA9685PW to which the servo is connected.
        :param reverse: Whether to reverse the degrees upon output.
        :param correction_degrees: Correction degrees to be added to any requested degrees to account for assembly
        errors (e.g., a servo not being mounted perfectly).
        """

        super().__init__(
            pca9685pw=pca9685pw,
            output_disable_pin=output_disable_pin,
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
                enabled: bool,
                degrees: float
        ):
            """
            Initialize the state.

            :param on: Whether servo is on.
            :param enabled: Whether servo is enabled.
            :param degrees: Degrees of rotation.
            """

            self.on = on
            self.enabled = enabled
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

            return self.on == other.on and self.enabled == other.enabled and self.degrees == other.degrees

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'On:  {self.on}, Enabled:  {self.enabled}, Degrees:  {self.degrees}'

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

        state: Servo.State = self.state

        if interval is not None:
            start_degrees = self.get_degrees()
            num_steps = int(abs(degrees - start_degrees) * 1.0)
            seconds_per_step = interval.total_seconds() / num_steps
            degrees_per_step = (degrees - start_degrees) / num_steps
            for step in range(num_steps):
                step_degrees = start_degrees + step * degrees_per_step
                self.set_state(Servo.State(on=state.on, enabled=state.enabled, degrees=step_degrees))
                time.sleep(seconds_per_step)

        self.set_state(Servo.State(on=state.on, enabled=state.enabled, degrees=degrees))

    def get_degrees(
            self
    ) -> float:
        """
        Get degrees of rotation.

        :return: Degrees.
        """

        state: Servo.State = self.state

        return state.degrees

    def enable(
            self
    ):
        """
        Enable the servo.
        """

        state: Servo.State = self.state
        self.set_state(Servo.State(on=state.on, enabled=True, degrees=state.degrees))

    def start(
            self
    ):
        """
        Start the servo at its current rotation.
        """

        state: Servo.State = self.state
        self.set_state(Servo.State(on=True, enabled=state.enabled, degrees=state.degrees))

    def stop(
            self
    ):
        """
        Stop the servo.
        """

        state: Servo.State = self.state
        self.set_state(Servo.State(on=False, enabled=state.enabled, degrees=state.degrees))

    def disable(
            self
    ):
        """
        Disable the stepper.
        """

        state: Servo.State = self.state
        self.set_state(Servo.State(on=state.on, enabled=False, degrees=state.degrees))

    def get_ui_elements(
            self
    ) -> List[Tuple[Union[str, Tuple[str, str]], str]]:
        """
        Get UI elements for the current component.

        :return: List of 2-tuples of (1) element key and (2) element content.
        """

        curr_state: Servo.State = self.state

        return [
            RpyFlask.get_switch(self.id, self.start, self.stop, None, curr_state.on),
            RpyFlask.get_range(self.id, int(self.min_degree), int(self.max_degree), 1, int(self.get_degrees()), False, False, [], [], [], False, self.set_degrees,None, False)
        ]

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

        super().__init__(Servo.State(on=False, enabled=False, degrees=degrees))

        self.driver = driver
        self.degrees = degrees
        self.min_degree = min_degree
        self.max_degree = max_degree


class StepperMotorDriver(ABC):
    """
    Abstract driver for stepper motors.
    """

    @abstractmethod
    def start(
            self
    ):
        """
        Start the driver.
        """

    @abstractmethod
    def step(
            self,
            stepper: 'Stepper',
            num_steps: int,
            time_to_step: timedelta
    ) -> Any:
        """
        Step the motor.

        :param stepper: Stepper.
        :param num_steps: Number of steps.
        :param time_to_step: Time to take.
        :return: Return value from the driver.
        """

    @abstractmethod
    def stop(
            self
    ):
        """
        Stop the driver.
        """


class StepperMotorDriverUln2003(StepperMotorDriver, ABC):
    """
    Abstract driver for stepper motors controlled by the ULN2003 integrated circuit, which is controlled via four GPIO
    pins.
    """

    def __init__(
            self,
            driver_pin_1: int,
            driver_pin_2: int,
            driver_pin_3: int,
            driver_pin_4: int
    ):
        """
        Initialize the driver.

        :param driver_pin_1: Driver GPIO pin 1.
        :param driver_pin_2: Driver GPIO pin 2.
        :param driver_pin_3: Driver GPIO pin 3.
        :param driver_pin_4: Driver GPIO pin 4.
        """

        self.driver_pin_1 = driver_pin_1
        self.driver_pin_2 = driver_pin_2
        self.driver_pin_3 = driver_pin_3
        self.driver_pin_4 = driver_pin_4

        self.driver_pins = [
            self.driver_pin_1,
            self.driver_pin_2,
            self.driver_pin_3,
            self.driver_pin_4
        ]


class StepperMotorDriverDirectUln2003(StepperMotorDriverUln2003):
    """
    Stepper motor driver that operates via the ULN2003 integrated circuit, which is directly controlled by four GPIO
    pins connected to the Raspberry Pi.
    """

    def __init__(
            self,
            driver_pin_1: int,
            driver_pin_2: int,
            driver_pin_3: int,
            driver_pin_4: int,
            limiter: Optional[Callable[[int], bool]]
    ):
        """
        Initialize the driver.

        :param driver_pin_1: Driver GPIO pin 1.
        :param driver_pin_2: Driver GPIO pin 2.
        :param driver_pin_3: Driver GPIO pin 3.
        :param driver_pin_4: Driver GPIO pin 4.
        :param limiter: Limiter function, which takes the stepping direction and returns a bool indicating whether the
        stepper has reached its limit and should stop stepping in the current direction.
        """

        super().__init__(
            driver_pin_1,
            driver_pin_2,
            driver_pin_3,
            driver_pin_4
        )

        self.limiter = limiter

        for driver_pin in self.driver_pins:
            gpio.setup(driver_pin, gpio.OUT)
            gpio.output(driver_pin, gpio.LOW)

        # use a half-step sequence across the gpio pins
        self.drive_sequence = [
            [gpio.HIGH, gpio.LOW, gpio.LOW, gpio.LOW],
            [gpio.HIGH, gpio.HIGH, gpio.LOW, gpio.LOW],
            [gpio.LOW, gpio.HIGH, gpio.LOW, gpio.LOW],
            [gpio.LOW, gpio.HIGH, gpio.HIGH, gpio.LOW],
            [gpio.LOW, gpio.LOW, gpio.HIGH, gpio.LOW],
            [gpio.LOW, gpio.LOW, gpio.HIGH, gpio.HIGH],
            [gpio.LOW, gpio.LOW, gpio.LOW, gpio.HIGH],
            [gpio.HIGH, gpio.LOW, gpio.LOW, gpio.HIGH],
        ]
        self.drive_sequence_idx = 0

    def start(
            self
    ):
        """
        Start the driver.
        """

        self.drive(0)

    def step(
            self,
            stepper: 'Stepper',
            num_steps: int,
            time_to_step: timedelta
    ) -> Any:
        """
        Step the motor.

        :param stepper: Stepper.
        :param num_steps: Number of steps.
        :param time_to_step: Time to step.
        :return: A boolean indicating whether the stepper hit a limiter.
        """

        delay_seconds_per_step = time_to_step.total_seconds() / abs(num_steps)

        # execute steps in the direction indicated
        direction = np.sign(num_steps)
        initial_state: Stepper.State = stepper.state
        initial_step = initial_state.step
        target_step = initial_step + num_steps
        curr_time = time.time()
        limited = False
        for next_step in range(initial_step + direction, target_step + direction, direction):

            # drive to the next half step and wait half the step delay
            self.drive(direction)
            time.sleep(delay_seconds_per_step / 2.0)

            # drive to the next half step, achieving the full step.
            self.drive(direction)

            # check for limiting
            if self.limiter is not None and self.limiter(direction):
                print(f'Stepper has been limited.')
                limited = True

            # update state. we do this at each step so that event listeners can react in real time as the stepper moves.
            new_time = time.time()
            new_state = Stepper.State(
                next_step,
                timedelta(seconds=new_time - curr_time)
            )
            super(Stepper, stepper).set_state(new_state)

            # stop moving if we've been limited
            if limited:
                break

            # mark new current time wait for the half-step delay
            curr_time = new_time
            time.sleep(delay_seconds_per_step / 2.0)

        result_state: Stepper.State = stepper.state
        if not limited and result_state.step != target_step:
            raise ValueError(f'Expected stepper state ({result_state.step}) to be goal state ({target_step}).')

        return limited

    def drive(
            self,
            direction: int
    ):
        """
        Drive the motor.

        :param direction: Direction, which must be -1, 0, or 1.
        """

        if direction != -1 and direction != 0 and direction != 1:
            raise ValueError('Invalid direction.')

        self.drive_sequence_idx = (self.drive_sequence_idx + direction) % len(self.drive_sequence)

        for pin_i, value in enumerate(self.drive_sequence[self.drive_sequence_idx]):
            gpio.output(self.driver_pins[pin_i], value)

    def stop(
            self
    ):
        """
        Stop the driver.
        """

        for driver_pin in self.driver_pins:
            gpio.output(driver_pin, gpio.LOW)


class StepperMotorDriverArduinoUln2003(StepperMotorDriverUln2003):
    """
    Stepper motor driver that operates via serial connection to an Arduino board, which controls the stepper motor via
    ULN2003 integrated circuit.
    """

    # Maximum number of steps is the maximum two-byte unsigned integer.
    MAX_TWO_BYTE_UNSIGNED_INT = 2 ** 16 - 1

    class Command(IntEnum):
        """
        Commands that can be sent to the Arduino.
        """

        INIT = 1
        STEP = 2
        STOP = 3

    def __init__(
            self,
            driver_pin_1: int,
            driver_pin_2: int,
            driver_pin_3: int,
            driver_pin_4: int,
            identifier: int,
            serial: LockingSerial,
            asynchronous: bool
    ):
        """
        Initialize the driver.

        :param driver_pin_1: Driver GPIO pin 1.
        :param driver_pin_2: Driver GPIO pin 2.
        :param driver_pin_3: Driver GPIO pin 3.
        :param driver_pin_4: Driver GPIO pin 4.
        :param identifier: Identifier.
        :param serial: Serial connection to the Arduino.
        :param asynchronous: Whether the driver should operate asynchronously.
        """

        super().__init__(
            driver_pin_1,
            driver_pin_2,
            driver_pin_3,
            driver_pin_4
        )

        self.identifier = identifier
        self.serial = serial
        self.asynchronous = asynchronous

    def start(self):
        """
        Start the driver.
        """

        success = bool(self.serial.write_then_read(
            StepperMotorDriverArduinoUln2003.Command.INIT.to_bytes(1) +
            self.identifier.to_bytes(1) +
            self.driver_pin_1.to_bytes(1) +
            self.driver_pin_2.to_bytes(1) +
            self.driver_pin_3.to_bytes(1) +
            self.driver_pin_4.to_bytes(1) +
            (-1).to_bytes(2, signed=True),
            True,
            1,
            False
        ))
        if not success:
            raise ValueError('Failed to initialize Arduino stepper motor driver.')

    def step(
            self,
            stepper: 'Stepper',
            num_steps: int,
            time_to_step: timedelta
    ) -> Any:
        """
        Step the motor.

        :param stepper: Stepper.
        :param num_steps: Number of steps.
        :param time_to_step: Time to take.
        :return: If operating synchronously, a float value indicating the number of steps skipped due to limiting. If
        operating asynchronously, a function that can be called to wait for the return value, which will be the stepping
        sequence identifier, the stepper identifier, and the number of steps skipped due to limiting.
        """

        if not (-32768 <= num_steps <= 32,767):
            raise ValueError(f'Steps must be in range of two-byte signed integer:  [32768, 32767]')

        ms_to_step = int(time_to_step.total_seconds() * 1000.0)
        if ms_to_step > StepperMotorDriverArduinoUln2003.MAX_TWO_BYTE_UNSIGNED_INT:
            raise ValueError(f'Maximum time (ms) to step:  {StepperMotorDriverArduinoUln2003.MAX_TWO_BYTE_UNSIGNED_INT}')

        bytes_to_write = (
            StepperMotorDriverArduinoUln2003.Command.STEP.to_bytes(1) +
            self.identifier.to_bytes(1) +
            num_steps.to_bytes(2, signed=True) +
            ms_to_step.to_bytes(2)
        )
        self.serial.write_then_read(bytes_to_write, True, 0, False)

        if self.asynchronous:
            return_value = self.wait_for_async_result
        else:
            identifier, return_value = self.wait_for_async_result()
            assert identifier == self.identifier

        return return_value

    def wait_for_async_result(
            self
    ) -> Tuple[int, float]:
        """
        Wait for asynchronous result.

        :return: 2-tuple of the stepper id and skipped steps.
        """

        result_bytes = self.serial.connection.read(5)
        assert len(result_bytes) == 5
        stepper_id = int.from_bytes(result_bytes[0:1], signed=False)
        skipped_steps = get_float(result_bytes[1:5])

        return stepper_id, skipped_steps

    def stop(self):
        """
        Stop the driver.
        """

        success = bool(self.serial.write_then_read(
            StepperMotorDriverArduinoUln2003.Command.STOP.to_bytes(1) +
            self.identifier.to_bytes(1),
            True,
            1,
            False
        ))
        if not success:
            raise ValueError('Failed to stop Arduino stepper motor driver.')


class StepperMotorDriverArduinoA4988(StepperMotorDriver):
    """
    Stepper motor driver that operates via serial connection to an Arduino board, which controls the stepper motor via
    A4988 integrated circuit.
    """

    # Maximum number of steps is the maximum two-byte unsigned integer.
    MAX_TWO_BYTE_UNSIGNED_INT = 2 ** 16 - 1

    class Command(IntEnum):
        """
        Commands that can be sent to the Arduino.
        """

        INIT = 1
        STEP = 2
        STOP = 3

    def __init__(
            self,
            driver_pin: int,
            direction_pin: int,
            identifier: int,
            serial: LockingSerial,
            asynchronous: bool
    ):
        """
        Initialize the driver.

        :param driver_pin: Driver GPIO pin.
        :param direction_pin: Direction pin.
        :param identifier: Identifier.
        :param serial: Serial connection to the Arduino.
        :param asynchronous: Whether the driver should operate asynchronously.
        """

        self.driver_pin = driver_pin
        self.direction_pin = direction_pin
        self.identifier = identifier
        self.serial = serial
        self.asynchronous = asynchronous

    def start(self):
        """
        Start the driver.
        """

        success = bool(self.serial.write_then_read(
            StepperMotorDriverArduinoA4988.Command.INIT.to_bytes(1) +
            self.identifier.to_bytes(1) +
            self.driver_pin.to_bytes(1) +
            self.direction_pin.to_bytes(2, signed=True),
            True,
            1,
            False
        ))
        if not success:
            raise ValueError('Failed to initialize Arduino stepper motor driver.')

    def step(
            self,
            stepper: 'Stepper',
            num_steps: int,
            time_to_step: timedelta
    ) -> Any:
        """
        Step the motor.

        :param stepper: Stepper.
        :param num_steps: Number of steps.
        :param time_to_step: Time to take.
        :return: If operating synchronously, a float value indicating the number of steps skipped due to limiting. If
        operating asynchronously, a function that can be called to wait for the return value, which will be the stepping
        sequence identifier, the stepper identifier, and the number of steps skipped due to limiting.
        """

        if not (-32768 <= num_steps <= 32,767):
            raise ValueError(f'Steps must be in range of two-byte signed integer:  [32768, 32767]')

        ms_to_step = int(time_to_step.total_seconds() * 1000.0)
        if ms_to_step > StepperMotorDriverArduinoA4988.MAX_TWO_BYTE_UNSIGNED_INT:
            raise ValueError(f'Maximum time (ms) to step:  {StepperMotorDriverArduinoA4988.MAX_TWO_BYTE_UNSIGNED_INT}')

        bytes_to_write = (
            StepperMotorDriverArduinoA4988.Command.STEP.to_bytes(1) +
            self.identifier.to_bytes(1) +
            num_steps.to_bytes(2, signed=True) +
            ms_to_step.to_bytes(2)
        )
        self.serial.write_then_read(bytes_to_write, True, 0, False)

        if self.asynchronous:
            return_value = self.wait_for_async_result
        else:
            identifier, return_value = self.wait_for_async_result()
            assert identifier == self.identifier

        return return_value

    def wait_for_async_result(
            self
    ) -> Tuple[int, float]:
        """
        Wait for asynchronous result.

        :return: 2-tuple of the stepper id and skipped steps.
        """

        result_bytes = self.serial.connection.read(5)
        assert len(result_bytes) == 5
        stepper_id = int.from_bytes(result_bytes[0:1], signed=False)
        skipped_steps = get_float(result_bytes[1:5])

        return stepper_id, skipped_steps

    def stop(self):
        """
        Stop the driver.
        """

        success = bool(self.serial.write_then_read(
            StepperMotorDriverArduinoA4988.Command.STOP.to_bytes(1) +
            self.identifier.to_bytes(1),
            True,
            1,
            False
        ))
        if not success:
            raise ValueError('Failed to stop Arduino stepper motor driver.')


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
        initial_state: Stepper.State = self.state
        num_steps = state.step - initial_state.step
        start_time = time.time()
        self.driver_step_return_value = self.driver.step(self, num_steps, state.time_to_step)
        end_time = time.time()

        # return value will be an integer of skipped steps if the driver is synchronous. we can update the state now. if
        # the driver is asynchronous, then we cannot update the stepper state here. it will need to be done elsewhere.
        if isinstance(self.driver_step_return_value, int):
            num_steps_taken = round(num_steps - self.driver_step_return_value)
            super().set_state(
                Stepper.State(
                    initial_state.step + num_steps_taken,
                    timedelta(seconds=end_time - start_time)
                )
            )

    def step(
            self,
            steps: int,
            time_to_step: timedelta
    ) -> Any:
        """
        Step the motor a number of steps.

        :param steps:  Number of steps.
        :param time_to_step: Amount of time to take.
        :return: Driver return value.
        """

        if self.reverse:
            steps = -steps

        initial_state: Stepper.State = self.state
        self.set_state(Stepper.State(initial_state.step + steps, time_to_step))

        return self.driver_step_return_value

    def step_degrees(
            self,
            degrees: float,
            time_to_step: timedelta
    ) -> Any:
        """
        Step the motor a number of degrees.

        :param degrees:  Number of degrees.
        :param time_to_step: Amount of time to take.
        :return: Driver return value.
        """

        return self.step(round(degrees * self.steps_per_degree), time_to_step)

    def start(
            self
    ):
        """
        Start the motor.
        """

        self.driver.start()

    def stop(
            self
    ):
        """
        Stop the motor.
        """

        self.driver.stop()

    def get_degrees(
            self
    ) -> float:
        """
        Get current degree rotation of the output shaft.

        :return: Degrees.
        """

        state: Stepper.State = self.state

        return (state.step / self.steps_per_degree) % 360.0

    def get_step(
            self
    ) -> int:
        """
        Get current step of the output shaft.

        :return: Step.
        """

        state: Stepper.State = self.state

        return state.step

    def get_ui_elements(
            self
    ) -> List[Tuple[Union[str, Tuple[str, str]], str]]:
        """
        Get UI elements for the current component.

        :return: List of 2-tuples of (1) element key and (2) element content.
        """

        return [
            RpyFlask.get_switch(self.id, self.start, self.stop, None, False)
        ]

    def __init__(
            self,
            full_steps_per_revolution: int,
            output_rotor_ratio: float,
            driver: StepperMotorDriver,
            reverse: bool
    ):
        """
        Initialize the motor.

        :param full_steps_per_revolution: Number of full steps per revolution.
        :param output_rotor_ratio: Output/rotor ratio (e.g., if the output shaft rotates one time per 100 rotations of
        the internal rotor, then this value would be 1/100). This is for stepper motors that have gearboxes. If there is
        no gearbox, then the output/rotor ratio is 1/1 = 1.0.
        :param driver: Stepper motor driver.
        :param reverse: Whether to reverse the stepper.
        """

        super().__init__(Stepper.State(0, timedelta(seconds=0)))

        self.full_steps_per_revolution = full_steps_per_revolution
        self.output_rotor_ratio = output_rotor_ratio
        self.driver = driver
        self.reverse = reverse

        self.steps_per_degree = (self.full_steps_per_revolution / self.output_rotor_ratio) / 360.0
        self.driver_step_return_value: Any = None
