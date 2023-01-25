import time

import numpy as np

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.motors import Servo, ServoDriverSoftwarePWM


def main():
    """
    This example moves a servo. It runs with the circuit described on page 184 of the tutorial.
    """

    setup()

    # create/start servo
    driver = ServoDriverSoftwarePWM(
        signal_pin=CkPin.GPIO18,
        min_pwm_high_ms=0.5,
        max_pwm_high_ms=2.5,
        pwm_high_offset_ms=0.0,
        min_degree=0.0,
        max_degree=180.0
    )
    servo = Servo(
        driver=driver,
        degrees=0.0,
        min_degree=0.0,
        max_degree=180.0
    )

    servo.start()

    # wave the servo back and forth through its full range
    for _ in range(10):
        if servo.get_degrees() == driver.min_degree:
            servo.set_degrees(driver.max_degree)
        else:
            servo.set_degrees(driver.min_degree)
        time.sleep(0.5)

    # step it through its range incrementally
    servo.set_degrees(0.0)
    degree_range = np.arange(driver.min_degree, driver.max_degree, 5)
    for degrees in degree_range:
        servo.set_degrees(degrees)
        time.sleep(0.25)
    for degrees in reversed(degree_range):
        servo.set_degrees(degrees)
        time.sleep(0.25)

    # clean up
    servo.stop()
    cleanup()


if __name__ == '__main__':
    main()
