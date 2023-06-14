from raspberry_py.gpio import CkPin
from raspberry_py.gpio.freenove.smart_car import Car, Wheel
from raspberry_py.gpio.robotics import RaspberryPyArm, RaspberryPyElevator
from raspberry_py.gpio.sensors import MjpgStreamer
from raspberry_py.rest.application import app

camera = MjpgStreamer(
    device='/dev/video0',
    width=640,
    height=480,
    fps=30,
    quality=100,
    port=8081
)
camera.id = 'camera-1'

car = Car(
    camera=camera,
    camera_pan_servo_correction_degrees=20.0,
    camera_tilt_servo_correction_degrees=-10.0,
    reverse_wheels=[Wheel.REAR_LEFT],
    connection_blackout_tolerance_seconds=2,
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
    arm_elevator_reversed=True,
    arm_elevator_correction_degrees=5,
    wrist_elevator_channel=12,
    wrist_elevator_correction_degrees=5,
    wrist_rotator_channel=13,
    wrist_rotator_reversed=True,
    wrist_rotator_correction_degrees=-5,
    pinch_servo_channel=14
)
arm.id = 'arm-1'
app.add_component(arm, True)
car.event(lambda s: arm.start() if s.on else arm.stop())

elevator = RaspberryPyElevator(
    left_stepper_pins=(CkPin.CE1, CkPin.CE0, CkPin.GPIO25, CkPin.GPIO24),
    right_stepper_pins=(CkPin.GPIO21, CkPin.GPIO20, CkPin.GPIO16, CkPin.GPIO12),
    bottom_limit_switch_input_pin=CkPin.MOSI,
    top_limit_switch_input_pin=CkPin.MISO,
    location_mm=0.0,
    steps_per_mm=38.5,
    reverse_right_stepper=True
)
elevator.id = 'elevator-1'
app.add_component(elevator, True)
car.event(lambda s: elevator.start() if s.on else elevator.stop())
