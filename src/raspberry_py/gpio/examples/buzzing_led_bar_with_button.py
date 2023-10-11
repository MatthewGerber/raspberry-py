import time
from datetime import timedelta

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import TwoPoleButton
from raspberry_py.gpio.lights import LedBar
from raspberry_py.gpio.sounds import ActiveBuzzer


def main():
    """
    This example combines buzzer_with_button.py and led_bar.py, such that pressing the button causes the LED bar to
    flow back and forth. The buzzer sounds when the LED reaches either end of the bar.
    """

    setup()

    # create button
    button = TwoPoleButton(input_pin=CkPin.GPIO18, bounce_time_ms=200, read_delay_ms=50)

    # create led bar
    led_bar = LedBar(
        output_pins=[
            CkPin.GPIO21,
            CkPin.GPIO20,
            CkPin.GPIO27,
            CkPin.GPIO22,
            CkPin.CE1,
            CkPin.GPIO5,
            CkPin.GPIO6,
            CkPin.GPIO13,
            CkPin.GPIO19,
            CkPin.GPIO26
        ],
        reverse=True
    )

    # flow the led bar back and forth 10 times when the button is pressed
    button.event(lambda s: [led_bar.flow(0.03) for _ in range(10)] if s.pressed else None)

    # create buzzer
    buzzer = ActiveBuzzer(output_pin=CkPin.GPIO17)

    # buzz when the led reaches either end
    led_bar.event(
        lambda s: buzzer.buzz(timedelta(seconds=0.2)) if s.illuminated_led_index in [0, 9] else None,
        synchronous=False
    )

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
