from datetime import timedelta

from flask import Flask

from rpi.gpio import setup, CkPin
from rpi.gpio.motors import Stepper

app = Flask(__name__)

setup()

# create/start stepper
stepper = Stepper(
    poles=32,
    output_rotor_ratio=1/64.0,
    driver_pin_1=CkPin.GPIO18,
    driver_pin_2=CkPin.GPIO23,
    driver_pin_3=CkPin.GPIO24,
    driver_pin_4=CkPin.GPIO25
)

stepper.start()


@app.route('/')
def hello_world():
    stepper.step(180, timedelta(seconds=2))
