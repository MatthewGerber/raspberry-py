from flask_cors import CORS

from rpi.gpio import setup, CkPin
from rpi.gpio.lights import LED
from rpi.rest.application import app

# allow cross-site access from an html front-end
CORS(app)

# set up gpio
setup()

# create an led and set its identifier. all components get a random identifier upon creation, but since this is the
# identifier that gets used in rest calls, something short is convenient.
led = LED(output_pin=CkPin.GPIO4)
led.id = 'led-1'

# add led to rest application
app.add_component(led)
