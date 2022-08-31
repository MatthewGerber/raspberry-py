from rpi.gpio import setup, CkPin
from rpi.gpio.lights import LED
from rpi.rest import application
from rpi.rest.application import add_component

# demonstrate a rest application that provides a single led
app = application.get()
setup()
led = LED(output_pin=CkPin.GPIO17)
led.id = 'led-1'
add_component(led)
