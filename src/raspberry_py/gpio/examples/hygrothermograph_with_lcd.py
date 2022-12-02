import time
from datetime import datetime

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.displays import Lcd1602
from raspberry_py.gpio.sensors import Hygrothermograph


def main():
    """
    This example displays the values of a hygrothermograph on an LCD, as shown on pages 245 (for the LCD) and 255 (for
    the hygrothermograph) of the tutorial.
    """

    setup()

    lcd = Lcd1602(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], pcf8574_address=Lcd1602.Pcf8574.PCF8574_ADDRESS)
    lcd.begin(2)  # set number of LCD lines

    def update_lcd(
            state: Hygrothermograph.State
    ):
        """
        Update the LCD display.

        :param state: New hygrothermograph state.
        """

        lcd.set_cursor(0, 0)  # set cursor position
        lcd.message(f'{state.humidity:.0f}% (H) @ {state.temperature_f:.0f} (F)\n')
        lcd.message(datetime.now().strftime('    %H:%M:%S'))

    sensor = Hygrothermograph(pin=CkPin.GPIO17)
    sensor.event(
        action=update_lcd,
        trigger=lambda s: s.status == Hygrothermograph.State.Status.OK
    )
    try:
        while True:
            sensor.read(5)
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    lcd.clear()
    lcd.pcf8574.destroy()
    cleanup()


if __name__ == '__main__':
    main()
