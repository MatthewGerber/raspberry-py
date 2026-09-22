import RPi.GPIO as gpio

from raspberry_py.gpio import CkPin, setup
from raspberry_py.gpio.lights import LED
from raspberry_py.rest.application import app

setup(gpio.BOARD)

led = LED(output_pin=CkPin.GPIO4)
led.id = 'led-1'
app.add_component(led)
app.start(__name__)