import time

from rpi.gpio import setup, cleanup, Clock
from rpi.gpio.lights import LED
from rpi.gpio.switches import TwoPoleButton


def main():
    """
    This example switches an LED on and off using a button. It runs with the circuit described on page 59 of the
    tutorial.
    """

    setup()

    # create an led on output pin 11
    led = LED(output_pin=11)

    # create a button on input pin 12
    button = TwoPoleButton(input_pin=12)

    # create a clock that ticks as quickly as possible. this will be the event source for updating the button's state.
    clock = Clock(tick_interval_seconds=None)

    # update the button state each clock tick
    clock.add_listener(
        trigger=lambda clock_state: True,
        event=lambda: button.update()
    )

    # turn the led on when the button is pressed
    button.add_listener(
        trigger=lambda button_state: True,
        event=lambda: led.set(LED.State(on=button.get().pressed))
    )

    # start clock and run for 10 seconds
    clock.start()
    print('You have 20 seconds to press the button...')
    time.sleep(20)
    clock.stop()

    cleanup()


if __name__ == '__main__':
    main()
