import time

from raspberry_py.gpio import setup, cleanup, CkPin
from raspberry_py.gpio.controls import TwoPoleButton
from raspberry_py.gpio.lights import LedBar
from raspberry_py.gpio.sounds import PassiveBuzzer


def main():
    """
    This example combines buzzer_with_button.py and led_bar.py, such that pressing the button causes the LED bar to
    flow back and forth. The active buzzer is replaced with a passive buzzer controlled with software PWM, such that
    the alarm oscillates from low to high pitch with the flow of the LED bar.
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

    # create buzzer
    buzzer = PassiveBuzzer(output_pin=CkPin.GPIO17)

    # flow the led bar back and forth when the button is pressed. start the buzzer before the flow, and stop it after.
    button.event(
        lambda s:
        (
            buzzer.start(0.0),
            led_bar.flow(0.25),
            buzzer.stop()
        ) if s.pressed else None,
        synchronous=False
    )

    # set buzzer frequency to match illuminated led
    led_bar.event(
        lambda s: buzzer.set_frequency(
            1.0 - s.illuminated_led_index / (len(led_bar) - 1)
        ) if s.illuminated_led_index is not None else None,
        synchronous=False
    )

    print('You have 20 seconds to press the button...')
    time.sleep(20)

    cleanup()


if __name__ == '__main__':
    main()
