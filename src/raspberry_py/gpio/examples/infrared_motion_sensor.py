import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.lights import LED
from raspberry_py.gpio.sensors import InfraredMotionSensor


def main():
    """
    This example senses motion and blinks an LED when it is detected. It runs with the circuit described on page 273 of
    the tutorial.
    """

    setup()

    led = LED(output_pin=CkPin.GPIO18)
    sensor = InfraredMotionSensor(sensor_pin=CkPin.GPIO17)
    sensor.event(lambda s: led.turn_on() if s.motion_detected else led.turn_off())
    try:
        time.sleep(300)
    except KeyboardInterrupt:
        pass

    led.turn_off()
    cleanup()


if __name__ == '__main__':
    main()
