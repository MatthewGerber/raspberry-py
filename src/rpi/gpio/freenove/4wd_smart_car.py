from smbus2 import SMBus

from rpi.gpio import Component
from rpi.gpio.integrated_circuits import PulseWaveModulatorPCA9685PW
from rpi.gpio.motors import DcMotor, DcMotorDriverPCA9685PW


class Car(Component):

    class State(Component.State):

        def __eq__(self, other: object) -> bool:
            return False

        def __str__(self) -> str:
            return ''

    def set_speed(
            self,
            speed: int
    ):
        for wheel in self.wheels:
            wheel.set_speed(speed)

    def __init__(
            self
    ):
        """
        Initialize the car
        """

        super().__init__(Car.State())

        i2c_bus = SMBus('/dev/i2c-1')

        pca9685pw = PulseWaveModulatorPCA9685PW(
            bus=i2c_bus,
            address=PulseWaveModulatorPCA9685PW.PCA9685PW_ADDRESS
        )
        pca9685pw.set_pwm_frequency(50)

        # 4 wheel motors use PWM channels 0-7 (2 channels per motor)
        self.wheels = [
            DcMotor(
                driver=DcMotorDriverPCA9685PW(
                    pca9685pw=pca9685pw,
                    motor_channel_1=motor_channel_1,
                    motor_channel_2=motor_channel_2
                ),
                speed=0
            )
            for motor_channel_1, motor_channel_2 in [(0, 1), (2, 3), (4, 5), (6, 7)]
        ]
        (
            self.front_left_wheel,
            self.rear_left_wheel,
            self.rear_right_wheel,
            self.front_right_wheel
        ) = self.wheels

        # 8 servos use PWM channels 8-15 (1 channel per servo)
