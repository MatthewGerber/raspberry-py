from typing import List

from raspberry_py.gpio import Component
from raspberry_py.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from raspberry_py.gpio.motors import Servo, ServoDriverPCA9685PW


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
                x_rotation: float,
                z_rotation: float,
                wrist_rotation: float,
                pinch: float
        ):
            """
            Initialize the state.

            :param x_rotation: Rotation around the x axis.
            :param z_rotation: Rotation around the z axis.
            :param wrist_rotation: Wrist rotation.
            :param pinch: Pinch.
            """

            self.x_rotation = x_rotation
            self.z_rotation = z_rotation
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
                self.x_rotation == other.x_rotation and
                self.z_rotation == other.z_rotation and
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
                f'x={self.x_rotation:.1f}, z={self.z_rotation:.1f}, wrist={self.wrist_rotation:.1f}, '
                f'pinch={self.pinch:.1f}'
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

    def set_x(
            self,
            rotation: float
    ):
        """
        Set x rotation.

        :param rotation: Rotation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            x_rotation=rotation,
            z_rotation=self.state.z_rotation,
            wrist_rotation=self.state.wrist_rotation,
            pinch=self.state.pinch
        ))

    def set_z(
            self,
            rotation: float
    ):
        """
        Set z rotation.

        :param rotation: Rotation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            x_rotation=self.state.x_rotation,
            z_rotation=rotation,
            wrist_rotation=self.state.wrist_rotation,
            pinch=self.state.pinch
        ))

    def set_wrist(
            self,
            rotation: float
    ):
        """
        Set wrist rotation.

        :param rotation: Rotation.
        """

        self.state: RaspberryPyArm.State
        self.set_state(RaspberryPyArm.State(
            x_rotation=self.state.x_rotation,
            z_rotation=self.state.z_rotation,
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
            x_rotation=self.state.x_rotation,
            z_rotation=self.state.z_rotation,
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

        self.x_servo.set_degrees(state.x_rotation)
        self.z_servo.set_degrees(state.z_rotation)
        self.wrist_servo.set_degrees(state.wrist_rotation)
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
            x_servo_channel: int,
            z_servo_channel: int,
            wrist_servo_channel: int,
            pinch_servo_channel: int
    ):
        """
        Initialize the arm.

        :param pwm: Pulse-wave modulator.
        :param x_servo_channel: Channel for x-axis servo.
        :param z_servo_channel: Channel for z-axis servo.
        :param wrist_servo_channel: Channel for wrist servo.
        :param pinch_servo_channel: Channel for pinch servo.
        """

        super().__init__(RaspberryPyArm.State(0, 0, 0, 0))

        self.pwm = pwm
        self.x_servo_channel = x_servo_channel
        self.z_servo_channel = z_servo_channel
        self.wrist_servo_channel = wrist_servo_channel
        self.pinch_servo_channel = pinch_servo_channel

        self.x_servo = Servo(
            driver=ServoDriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.x_servo_channel,
                min_degree=0.0,
                min_degree_pulse_width_ms=1.0,
                max_degree=180.0,
                max_degree_pulse_width_ms=2.0
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.x_servo.id = 'arm-x'

        self.z_servo = Servo(
            driver=ServoDriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.z_servo_channel,
                min_degree=0.0,
                min_degree_pulse_width_ms=1.0,
                max_degree=180.0,
                max_degree_pulse_width_ms=2.0
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.z_servo.id = 'arm-z'

        self.wrist_servo = Servo(
            driver=ServoDriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.wrist_servo_channel,
                min_degree=0.0,
                min_degree_pulse_width_ms=1.0,
                max_degree=180.0,
                max_degree_pulse_width_ms=2.0
            ),
            degrees=90.0,
            min_degree=0.0,
            max_degree=180.0
        )
        self.wrist_servo.id = 'arm-wrist'

        self.pinch_servo = Servo(
            driver=ServoDriverPCA9685PW(
                pca9685pw=pwm,
                servo_channel=self.pinch_servo_channel,
                min_degree=0.0,
                min_degree_pulse_width_ms=1.0,
                max_degree=180.0,
                max_degree_pulse_width_ms=2.0
            ),
            degrees=0.0,
            min_degree=0.0,
            max_degree=90.0
        )
        self.pinch_servo.id = 'arm-pinch'

        self.servos = [
            self.x_servo,
            self.z_servo,
            self.wrist_servo,
            self.pinch_servo
        ]
