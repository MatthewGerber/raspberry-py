import RPi.GPIO as gpio

from raspberry_py.gpio import CkPin, setup
from raspberry_py.gpio.motors import DcMotor, DcMotorDriverL293D
from raspberry_py.rest.application import app

setup(gpio.BOARD)

motor = DcMotor(
    driver=DcMotorDriverL293D(
        enable_pin=CkPin.GPIO22,
        in_1_pin=CkPin.GPIO27,
        in_2_pin=CkPin.GPIO17
    ),
    speed=0
)
motor.id = 'motor-1'
app.add_component(motor)
app.start(__name__)

