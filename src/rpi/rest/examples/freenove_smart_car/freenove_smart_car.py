from rpi.gpio.freenove.smart_car import Car, Wheel
from rpi.rest.application import app

car = Car(
    camera_pan_servo_correction_degrees=5.0,
    camera_tilt_servo_correction_degrees=-15.0,
    reverse_wheels=[Wheel.REAR_LEFT],
    camera_width=160,
    camera_height=120,
    connection_blackout_tolerance_seconds=2
)
car.id = 'car-1'

app.add_component(car, True)
