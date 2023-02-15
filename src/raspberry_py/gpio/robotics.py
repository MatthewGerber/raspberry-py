from typing import List

from raspberry_py.gpio import Component
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import Servo, Sg90DriverPCA9685PW


class RaspberryPyArm(Component):
    """
    A simple robotic arm. See https://matthewgerber.github.io/raspberry-py/raspberry-py/robotic-arm.html for details.
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
