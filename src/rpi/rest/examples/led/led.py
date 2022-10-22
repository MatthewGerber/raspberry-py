from rpi.gpio import CkPin
from rpi.gpio.lights import LED
from rpi.rest.application import app

led = LED(output_pin=CkPin.GPIO4)
led.id = 'led-1'

app.add_component(led, True)
