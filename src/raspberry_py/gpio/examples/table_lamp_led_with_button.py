import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import TwoPoleButton
from raspberry_py.gpio.lights import LED


def main():
    """
    This example switches an LED on and off using a button, but in the "table lamp" style where the first press turns
    the LED on, the second press turns it off, etc. It runs with the circuit described on page 59 of the tutorial.
    """

    setup()

    # create an led
    led = LED(output_pin=CkPin.GPIO17)

    # create a button
    button = TwoPoleButton(input_pin=CkPin.GPIO18, bounce_time_ms=50, read_delay_ms=50)

    # turn the led on when the button is pressed and off when pressed again
    button.event(
        lambda _: led.turn_off() if button.is_pressed() and led.is_on()
        else led.turn_on() if button.is_pressed() and led.is_off()
        else None
    )

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
