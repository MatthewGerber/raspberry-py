from raspberry_py.gpio import CkPin
from raspberry_py.gpio.power import Relay
from raspberry_py.rest.application import app

relay = Relay(
    transistor_base_pin=CkPin.GPIO21
)
relay.id = 'relay-1'
app.add_component(relay, True)
