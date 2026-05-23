from raspberry_py.gpio.lights import LedStrip
from rpi_ws281x import Color


def main():

    led_strip = LedStrip(
        led_count=144,
        led_pin=12
    )

    while True:
        try:
            led_strip.theater_chase(Color(0, 255, 0), iterations=10, wait_ms=50)
        except KeyboardInterrupt:
            led_strip.turn_off()
            break
        except:
            pass


if __name__ == '__main__':
    main()
