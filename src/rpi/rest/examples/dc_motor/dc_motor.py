from rpi.gpio import CkPin
from rpi.gpio.motors import DcMotor
from rpi.rest.application import app

motor = DcMotor(
    enable_pin=CkPin.GPIO22,
    in_1_pin=CkPin.GPIO27,
    in_2_pin=CkPin.GPIO17,
    speed=0
)
motor.id = 'motor-1'

app.add_component(motor)
