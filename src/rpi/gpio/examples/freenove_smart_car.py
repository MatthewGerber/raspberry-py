import time

from rpi.gpio import setup
from rpi.gpio.freenove.smart_car import Car


def main():

    setup()

    car = Car()

    car.start()

    time.sleep(1)

    for i in range(90, 180):
        car.camera_tilt_servo.set_degrees(i)
        time.sleep(0.025)
        print(str(i))

    for i in range(180, 75, -1):
        car.camera_tilt_servo.set_degrees(i)
        time.sleep(0.025)
        print(str(i))

    car.camera_tilt_servo.set_degrees(90)

    for i in range(90, 180):
        car.camera_pan_servo.set_degrees(i)
        time.sleep(0.025)
        print(str(i))

    for i in range(180, 0, -1):
        car.camera_pan_servo.set_degrees(i)
        time.sleep(0.025)
        print(str(i))

    car.camera_pan_servo.set_degrees(90)


if __name__ == '__main__':
    main()
