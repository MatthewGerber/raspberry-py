import time

from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LED


def main():

    setup()

    # create an led on output pin 11
    led = LED(output_pin=11)

    # set on for 1 second, then off.
    led.set(LED.State(on=True))
    time.sleep(1)
    led.set(LED.State(on=False))

    cleanup()


if __name__ == '__main__':
    main()
