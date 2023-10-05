import time
from datetime import timedelta

from raspberry_py.gpio import setup
from raspberry_py.gpio.freenove.smart_car import Car, Wheel
from raspberry_py.gpio.sensors import Camera


def main():

    setup()

    camera = Camera(
        device='/dev/video0',
        width=160,
        height=120,
        fps=30,
        run_face_detection=True,
        circle_detected_faces=True,
        face_detection_callback=None
    )
    camera.id = 'camera-1'

    car = Car(
        camera=camera,
        camera_pan_servo_correction_degrees=5.0,
        camera_tilt_servo_correction_degrees=-15.0,
        reverse_wheels=[Wheel.REAR_LEFT]
    )

    car.start()

    for wheel in car.wheels:
        wheel.set_speed(50)
        time.sleep(0.5)

    for wheel in car.wheels:
        wheel.set_speed(-50)
        time.sleep(0.5)

    for wheel in car.wheels:
        wheel.set_speed(0)

    car.set_wheel_speed(car.left_wheels, 50)
    time.sleep(0.5)
    car.set_wheel_speed(car.right_wheels, 50)
    time.sleep(0.5)
    car.set_wheel_speed(car.wheels, 0)

    car.camera_tilt_servo.set_degrees(degrees=180.0, interval=timedelta(seconds=0.5))
    car.camera_tilt_servo.set_degrees(degrees=70.0, interval=timedelta(seconds=0.5))
    car.camera_tilt_servo.set_degrees(90)

    car.camera_pan_servo.set_degrees(degrees=180.0, interval=timedelta(seconds=0.5))
    car.camera_pan_servo.set_degrees(degrees=0.0, interval=timedelta(seconds=1.0))
    car.camera_pan_servo.set_degrees(90)


if __name__ == '__main__':
    main()
