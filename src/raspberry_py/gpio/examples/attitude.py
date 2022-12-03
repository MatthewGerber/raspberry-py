#!/usr/bin/env python3
########################################################################
# Filename    : attitude.py
# Description : Read data of MPU6050.
# author      : www.freenove.com
# modification: 2019/12/28
########################################################################
import time

from raspberry_py.gpio import cleanup
from raspberry_py.gpio.freenove.mpu6050 import MPU6050


def main():

    print('Program is starting ... ')

    mpu = MPU6050.MPU6050()
    mpu.dmp_initialize()
    try:
        while True:

            accel = mpu.get_acceleration()  # get accelerometer data
            gyro = mpu.get_rotation()  # get gyroscope data

            print("a/g:%d\t%d\t%d\t%d\t%d\t%d " % (
                accel[0], accel[1], accel[2],
                gyro[0], gyro[1], gyro[2]
            ))

            print("a/g:%.2f g\t%.2f g\t%.2f g\t%.2f d/s\t%.2f d/s\t%.2f d/s" % (
                accel[0] / 16384.0, accel[1] / 16384.0, accel[2] / 16384.0,
                gyro[0] / 131.0, gyro[1] / 131.0, gyro[2] / 131.0
            ))

            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    cleanup()


if __name__ == '__main__':
    main()
