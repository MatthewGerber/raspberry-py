import RPi.GPIO as gpio
import time

LED_PIN = 11


def setup():

    gpio.setmode(gpio.BOARD)
    gpio.setup(LED_PIN, gpio.OUT)
    gpio.output(LED_PIN, gpio.LOW)


def blink():

    while True:

        time.sleep(1)
        gpio.output(LED_PIN, gpio.HIGH)
        time.sleep(1)
        gpio.output(LED_PIN, gpio.LOW)


def cleanup():

    gpio.cleanup()


def main():

    setup()

    try:
        blink()
    except:
        cleanup()


if __name__ == '__main__':
    main()
