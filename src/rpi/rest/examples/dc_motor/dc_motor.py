from flask_cors import CORS

from rpi.gpio import setup, CkPin
from rpi.gpio.motors import DcMotor
from rpi.rest.application import app

# allow cross-site access from an html front-end
CORS(app)

# set up gpio
setup()

# create a motor and set its identifier. all components get a random identifier upon creation, but since this is the
# identifier that gets used in rest calls, something short is convenient.
motor = DcMotor(
    enable_pin=CkPin.GPIO22,
    in_1_pin=CkPin.GPIO27,
    in_2_pin=CkPin.GPIO17,
    speed=0
)

motor.id = 'motor-1'
motor.start()

# add motor to rest application
app.add_component(motor)
