from raspberry_py.gpio.freenove.smart_car import Car, Wheel
from raspberry_py.gpio.robotics import RaspberryPyArm
from raspberry_py.rest.application import app

car = Car(
    camera_pan_servo_correction_degrees=15.0,
    camera_tilt_servo_correction_degrees=-10.0,
    reverse_wheels=[Wheel.REAR_LEFT],
    camera_width=160,
    camera_height=120,
    connection_blackout_tolerance_seconds=2,
    run_face_detection=False,
    battery_min=72.54902,
    battery_max=83.52941
)
car.id = 'car-1'
app.add_component(car, True)

arm = RaspberryPyArm(
    pwm=car.pwm,
    base_rotator_channel=10,
    base_rotator_reversed=True,
    arm_elevator_channel=11,
    arm_elevator_correction_degrees=-5,
    wrist_elevator_channel=12,
    wrist_elevator_reversed=True,
    wrist_elevator_correction_degrees=-5,
    wrist_rotator_channel=13,
    wrist_rotator_reversed=True,
    wrist_rotator_correction_degrees=-5,
    pinch_servo_channel=14
)
arm.id = 'arm-1'
app.add_component(arm, True)
car.event(lambda s: arm.start() if s.on else arm.stop())
