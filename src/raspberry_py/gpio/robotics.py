import time
from datetime import timedelta
from typing import List, Tuple

from raspberry_py.gpio import Component, CkPin
from raspberry_py.gpio.controls import LimitSwitch
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import Servo, Sg90DriverPCA9685PW, Stepper


class RaspberryPyArm(Component):
    """
    A robotic arm. See https://matthewgerber.github.io/raspberry-py/raspberry-py/robotic-arm.html for details.
    """

    class State(Component.State):
        """
        Arm state.
        """

        def __init__(
                self,
                base_rotation: float,
                arm_elevation: float,
                wrist_elevation: float,
                wrist_rotation: float,
                pinch: float
        ):
            """
            Initialize the state.

            :param base_rotation: Base rotation.
            :param arm_elevation: Arm elevation.
            :param wrist_elevation: Wrist elevation.
            :param wrist_rotation: Wrist rotation.
            :param pinch: Pinch.
            """

            self.base_rotation = base_rotation
            self.arm_elevation = arm_elevation
            self.wrist_elevation = wrist_elevation
            self.wrist_rotation = wrist_rotation
            self.pinch = pinch

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, RaspberryPyArm.State):
                raise ValueError(f'Expected a {RaspberryPyArm.State}')

            return (
                self.base_rotation == other.base_rotation and
                self.arm_elevation == other.arm_elevation and
                self.wrist_elevation == other.wrist_elevation and
                self.wrist_rotation == other.wrist_rotation and
                self.pinch == other.pinch
            )

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return (
                f'({self.base_rotation:.1f},{self.arm_elevation:.1f},{self.wrist_elevation},'
                f'{self.wrist_rotation:.1f},{self.pinch:.1f}'
            )

    def start(
            self
    ):
        """
        Start the arm.
        """

        for servo in self.servos:
            servo.start()

    def stop(
            self
    ):
        """
        Stop the arm.
        """

        for servo in self.servos:
            servo.stop()

    def set_base_rotation(
            self,
            rotation: float
    ):
        """
        Set base rotation.

        :param rotation: Rotation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            base_rotation=rotation,
            arm_elevation=self.state.arm_elevation,
            wrist_elevation=self.state.wrist_elevation,
            wrist_rotation=self.state.wrist_rotation,
            pinch=self.state.pinch
        ))

    def set_arm_elevation(
            self,
            elevation: float
    ):
        """
        Set arm elevation.

        :param elevation: Elevation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            base_rotation=self.state.base_rotation,
            arm_elevation=elevation,
            wrist_elevation=self.state.wrist_elevation,
            wrist_rotation=self.state.wrist_rotation,
            pinch=self.state.pinch
        ))

    def set_wrist_elevation(
            self,
            elevation: float
    ):
        """
        Set wrist elevation.

        :param elevation: Elevation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            base_rotation=self.state.base_rotation,
            arm_elevation=self.state.arm_elevation,
            wrist_elevation=elevation,
            wrist_rotation=self.state.wrist_rotation,
            pinch=self.state.pinch
        ))

    def set_wrist_rotation(
            self,
            rotation: float
    ):
        """
        Set wrist rotation.

        :param rotation: Rotation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            base_rotation=self.state.base_rotation,
            arm_elevation=self.state.arm_elevation,
            wrist_elevation=self.state.wrist_elevation,
            wrist_rotation=rotation,
            pinch=self.state.pinch
        ))

    def set_pinch(
            self,
            pinch: float
    ):
        """
        Set pinch.

        :param pinch: Pinch.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            base_rotation=self.state.base_rotation,
            arm_elevation=self.state.arm_elevation,
            wrist_elevation=self.state.wrist_elevation,
            wrist_rotation=self.state.wrist_rotation,
            pinch=pinch
        ))

    def set_state(
            self,
            state: 'Component.State'
    ):
        """
        Set state.

        :param state: State.
        """

        state: RaspberryPyArm.State

        self.base_rotator_servo.set_degrees(state.base_rotation)
        self.arm_elevator_servo.set_degrees(state.arm_elevation)
        self.wrist_elevator_servo.set_degrees(state.wrist_elevation)
        self.wrist_rotator_servo.set_degrees(state.wrist_rotation)
        self.pinch_servo.set_degrees(state.pinch)

        super().set_state(state)

    def get_components(
            self
    ) -> List[Component]:
        """
        Get a list of all GPIO circuit components in the arm.

        :return: List of components.
        """

        return self.servos

    def __init__(
            self,
            pwm: PulseWaveModulatorPCA9685PW,
            base_rotator_channel: int,
            arm_elevator_channel: int,
            wrist_elevator_channel: int,
            wrist_rotator_channel: int,
            pinch_servo_channel: int,
            base_rotator_reversed: bool = False,
            base_rotator_correction_degrees: float = 0.0,
            arm_elevator_reversed: bool = False,
            arm_elevator_correction_degrees: float = 0.0,
            wrist_elevator_reversed: bool = False,
            wrist_elevator_correction_degrees: float = 0.0,
            wrist_rotator_reversed: bool = False,
            wrist_rotator_correction_degrees: float = 0.0,
            pinch_reversed: bool = False,
            pinch_correction_degrees: float = 0.0
    ):
        """
        Initialize the arm.

        :param pwm: Pulse-wave modulator.
        :param base_rotator_channel: Base rotator servo channel.
        :param base_rotator_reversed: Whether base rotator servo is reversed.
        :param arm_elevator_channel: Arm elevator servo channel.
        :param arm_elevator_reversed: Whether arm elevator servo is reversed.
        :param wrist_elevator_channel: Wrist elevator servo channel.
        :param wrist_elevator_reversed: Wrist elevator servo is reversed.
        :param wrist_rotator_channel: Wrist rotator servo channel.
        :param wrist_rotator_reversed: Whether wrist rotator servo is reversed.
        :param pinch_servo_channel: Pinch servo channel.
        :param pinch_reversed: Whether pinch servo is reversed.
        """

        super().__init__(RaspberryPyArm.State(0, 0, 0, 0, 0))

        self.pwm = pwm
        self.base_rotator_channel = base_rotator_channel
        self.arm_elevator_channel = arm_elevator_channel
        self.wrist_elevator_channel = wrist_elevator_channel
        self.wrist_rotator_channel = wrist_rotator_channel
        self.pinch_servo_channel = pinch_servo_channel

        self.base_rotator_servo = Servo(
            driver=Sg90DriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.base_rotator_channel,
                reverse=base_rotator_reversed,
                correction_degrees=base_rotator_correction_degrees
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.base_rotator_servo.id = 'arm-base-rotator'

        self.arm_elevator_servo = Servo(
            driver=Sg90DriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.arm_elevator_channel,
                reverse=arm_elevator_reversed,
                correction_degrees=arm_elevator_correction_degrees
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.arm_elevator_servo.id = 'arm-elevator'

        self.wrist_elevator_servo = Servo(
            driver=Sg90DriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.wrist_elevator_channel,
                reverse=wrist_elevator_reversed,
                correction_degrees=wrist_elevator_correction_degrees
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.wrist_elevator_servo.id = 'arm-wrist-elevator'

        self.wrist_rotator_servo = Servo(
            driver=Sg90DriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.wrist_rotator_channel,
                reverse=wrist_rotator_reversed,
                correction_degrees=wrist_rotator_correction_degrees
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.wrist_rotator_servo.id = 'arm-wrist-rotator'

        self.pinch_servo = Servo(
            driver=Sg90DriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.pinch_servo_channel,
                reverse=pinch_reversed,
                correction_degrees=pinch_correction_degrees
            ),
            degrees=0.0,
            min_degree=0.0,
            max_degree=38.0
        )
        self.pinch_servo.id = 'arm-pinch'

        self.servos = [
            self.base_rotator_servo,
            self.arm_elevator_servo,
            self.wrist_elevator_servo,
            self.wrist_rotator_servo,
            self.pinch_servo
        ]


class RaspberryPyElevator(Component):
    """
    An elevator. See https://matthewgerber.github.io/raspberry-py/raspberry-py/elevator.html for details.
    """

    class State(Component.State):
        """
        Elevator state.
        """

        def __init__(
                self,
                location_mm: float
        ):
            """
            Initialize the state.

            :param location_mm: Location (mm).
            """

            self.location_mm = location_mm

        def __eq__(self, other: object) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, RaspberryPyElevator.State):
                raise ValueError(f'Expected a {RaspberryPyElevator.State}')

            return self.location_mm == other.location_mm

        def __str__(self) -> str:
            """
            Get string.

            :return: String.
            """

            return f'{self.location_mm}'

    def move_up_1_mm_1_sec(
            self
    ):
        """
        Move up 1mm in 1s.
        """

        self.move(1, timedelta(seconds=1))

    def move_down_1_mm_1_sec(
            self
    ):
        """
        Move down 1mm in 1s.
        """

        self.move(-1, timedelta(seconds=1))

    def move(
            self,
            mm: int,
            time_to_move: timedelta
    ):
        """
        Move the elevator.

        :param mm: Signed number of millimeters to move (positive is up and negative is down).
        :param time_to_move: Amount of time to take when moving.
        """

        self.state: RaspberryPyElevator.State

        steps = round(mm * self.steps_per_mm)
        self.stepper_left.step(steps, time_to_move)
        self.set_state(RaspberryPyElevator.State(self.state.location_mm + steps))

    def step_left(
            self,
            steps: int,
            time_to_step: timedelta
    ):
        """
        Step the left motor.

        :param steps: Number of steps.
        :param time_to_step: Time to take.
        """

        self.asynchronize_steppers()
        self.stepper_left.step(steps, time_to_step)
        self.synchronize_steppers()

    def step_right(
            self,
            steps: int,
            time_to_step: timedelta
    ):
        """
        Step the right motor.

        :param steps: Number of steps.
        :param time_to_step: Time to take.
        """

        self.asynchronize_steppers()
        self.stepper_right.step(steps, time_to_step)
        self.synchronize_steppers()

    def start(
            self
    ):
        """
        Start the elevator.
        """

        self.stepper_left.start()
        self.stepper_right.start()

    def stop(
            self
    ):
        """
        Stop the elevator.
        """

        self.stepper_left.stop()
        self.stepper_right.stop()

    def synchronize_steppers(
            self
    ):
        """
        Synchronize the steppers such that their movements are identical in opposite directions as required by the
        elevator's design.
        """

        self.asynchronize_steppers()

        # synchronize the motors in reverse, as they are mounted opposite each other.
        self.stepper_left.event(lambda s: self.stepper_right.step(
            -s.step - self.stepper_right.get_step(),
            timedelta(0)
        ))

    def asynchronize_steppers(
            self
    ):
        """
        Asynchronize the steppers such that they can move independently.
        """

        self.stepper_left.events.clear()

    def platform_has_reached_limit(
            self,
            current_state: Stepper.State,
            next_state: Stepper.State
    ) -> bool:
        """
        Check whether the platform has reached a limit.

        :return: True if the platform has reached a limit.
        """

        return (
            (self.bottom_limit_switch.is_pressed() and next_state.step < current_state.step) or
            (self.top_limit_switch.is_pressed() and next_state.step > current_state.step)
        )

    def align_gears_and_mount(
            self
    ):
        """
        Align gears and mount the elevator. The following steps are executed in sequence:

          1. The left stepper runs until CTRL+C is pressed.
          2. The right stepper runs until CTRL+C is pressed. At this point, the gears must be oriented identically.
          3. Wait for CTRL+C. This gives you time to move the platform to the elevator posts and prepare for
          lowering. Press CTRL+C when ready for lowering.
          4. The steppers will rotate until CTRL+C is pressed, such that the platform will be lowered onto the mount.

        This function must be called from the shell in order for CTRL+C to be handled correctly.
        """

        self.asynchronize_steppers()

        print('Wait until the left stepper is aligned, then press CTRL+C...')
        try:
            while True:
                self.stepper_left.step(300, timedelta(seconds=5))
        except KeyboardInterrupt:
            pass

        print('Wait until the right stepper is aligned, then press CTRL+C...')
        try:
            while True:
                self.stepper_right.step(300, timedelta(seconds=5))
        except KeyboardInterrupt:
            pass

        print('Wait until the platform is ready to be lowered, then press CTRL+C...')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.synchronize_steppers()

        print('Wait until the platform is lowered, then press CTRL+C...')
        try:
            while True:
                self.move(-20, timedelta(seconds=5))
        except KeyboardInterrupt:
            pass

    def __init__(
            self,
            left_stepper_pins: Tuple[CkPin, CkPin, CkPin, CkPin],
            right_stepper_pins: Tuple[CkPin, CkPin, CkPin, CkPin],
            bottom_limit_switch_input_pin: CkPin,
            top_limit_switch_input_pin: CkPin,
            location_mm: float,
            steps_per_mm: float,
            reverse_left_stepper: bool = False,
            reverse_right_stepper: bool = False
    ):
        """
        Initialize the elevator.

        :param left_stepper_pins: Left stepper pins, a 4-tuple in which the first element is the GPIO pin connected to
        the first input of the left stepper's driver, and so on.
        :param right_stepper_pins: Right stepper pins, a 4-tuple in which the first element is the GPIO pin connected to
        the first input of the right stepper's driver, and so on.
        :param bottom_limit_switch_input_pin: Input (reading) pin of the bottom-limit switch.
        :param top_limit_switch_input_pin: Input (reading) pin of the top-limit switch.
        :param location_mm: Current location.
        :param steps_per_mm: Number of steps per millimeter.
        :param reverse_left_stepper: Whether to reverse the left stepper.
        :param reverse_right_stepper: Whether to reverse the right stepper.
        """

        super().__init__(RaspberryPyElevator.State(location_mm))

        self.steps_per_mm = steps_per_mm

        self.bottom_limit_switch = LimitSwitch(input_pin=bottom_limit_switch_input_pin, bounce_time_ms=5)
        self.top_limit_switch = LimitSwitch(input_pin=top_limit_switch_input_pin, bounce_time_ms=5)

        if reverse_left_stepper:
            left_stepper_pins = list(reversed(left_stepper_pins))

        # we synchronize from the left stepper to the right, so we only need to put the limiter on the left.
        self.stepper_left = Stepper(
            poles=32,
            output_rotor_ratio=1 / 64.0,
            driver_pin_1=left_stepper_pins[0],
            driver_pin_2=left_stepper_pins[1],
            driver_pin_3=left_stepper_pins[2],
            driver_pin_4=left_stepper_pins[3],
            limiter=self.platform_has_reached_limit
        )

        if reverse_right_stepper:
            right_stepper_pins = list(reversed(right_stepper_pins))

        self.stepper_right = Stepper(
            poles=32,
            output_rotor_ratio=1 / 64.0,
            driver_pin_1=right_stepper_pins[0],
            driver_pin_2=right_stepper_pins[1],
            driver_pin_3=right_stepper_pins[2],
            driver_pin_4=right_stepper_pins[3]
        )

        self.synchronize_steppers()
