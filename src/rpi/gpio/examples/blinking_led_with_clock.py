import time

from rpi.gpio import setup, cleanup, Clock
from rpi.gpio.lights import LED


def main():
    """
    This example switches an LED on and off at regular intervals. It runs with the circuit described on page 53 of the
    tutorial.
    """

    setup()

    # create an led on output pin 11
    led = LED(output_pin=11)

    # create a clock that ticks each second
    clock = Clock(tick_interval_seconds=0.5)

    # alternate the led each clock tick
    clock.add_listener(
        trigger=lambda clock_state: True,
        event=lambda: led.set(LED.State(on=not led.get().on))
    )

    # start clock and run for 10 seconds
    clock.start()
    time.sleep(10)
    clock.stop()

    cleanup()


if __name__ == '__main__':
    main()
