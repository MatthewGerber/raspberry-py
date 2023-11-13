from raspberry_py.gpio import CkPin
from raspberry_py.gpio.power import Relay
from raspberry_py.gpio.sensors import Tachometer
from raspberry_py.rest.application import app

power = Relay(
    transistor_base_pin=CkPin.GPIO21
)
power.id = 'power-1'
app.add_component(power, True)

tachometer = Tachometer(
    reading_pin=CkPin.GPIO24,
    bounce_time_ms=1,
    read_delay_ms=0.1,
    low_readings_per_rotation=4,
    smoothing_factor=0.98
)
tachometer.id = 'tachometer-1'
app.add_component(tachometer, True)
