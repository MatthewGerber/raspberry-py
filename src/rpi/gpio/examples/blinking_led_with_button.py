import time

from rpi.gpio import setup, cleanup
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
    button = TwoPoleButton(input_pin=12, bounce_time_ms=50)

    # turn the led on when the button is pressed
    button.event(lambda _: led.turn_on() if button.is_pressed() else led.turn_off())

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
