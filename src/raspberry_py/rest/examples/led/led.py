from raspberry_py.gpio import CkPin
from raspberry_py.gpio.lights import LED
from raspberry_py.rest.application import app

led = LED(output_pin=CkPin.GPIO4)
led.id = 'led-1'
app.add_component(led, True)
