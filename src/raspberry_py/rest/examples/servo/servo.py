from raspberry_py.gpio import CkPin
from raspberry_py.gpio.motors import Servo, ServoDriverSoftwarePWM
from raspberry_py.rest.application import app


servo = Servo(
    driver=ServoDriverSoftwarePWM(
        signal_pin=CkPin.GPIO18,
        min_pwm_high_ms=0.5,
        max_pwm_high_ms=2.5,
        pwm_high_offset_ms=0.0,
        min_degree=0.0,
        max_degree=180.0
    ),
    degrees=0.0,
    min_degree=0.0,
    max_degree=180.0
)
servo.id = 'servo-1'
app.add_component(servo, True)
