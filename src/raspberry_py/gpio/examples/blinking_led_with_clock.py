import time

from raspberry_py.gpio import setup, cleanup, Clock, CkPin
from raspberry_py.gpio.lights import LED


def main():
    """
    This example switches an LED on and off at regular intervals. It runs with the circuit described on page 40 of the
    tutorial.
    """

    setup()

    # create an led
    led = LED(output_pin=CkPin.GPIO17)

    # create a clock that ticks each second
    clock = Clock(tick_interval_seconds=0.5)

    # alternate the led each clock tick
    clock.event(lambda _: led.turn_off() if led.is_on() else led.turn_on())

    # start clock and run for 10 seconds
    clock.start()
    time.sleep(10)
    clock.stop()

    cleanup()


if __name__ == '__main__':
    main()
