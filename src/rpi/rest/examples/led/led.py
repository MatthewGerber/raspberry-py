from flask_cors import CORS

from rpi.gpio import setup, CkPin
from rpi.gpio.lights import LED
from rpi.rest.application import app, add_component

# allow cross-site access from an html front-end
CORS(app)

setup()
led = LED(output_pin=CkPin.GPIO17)
led.id = 'led-1'
add_component(led)
