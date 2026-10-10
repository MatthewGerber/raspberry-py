from datetime import datetime
from time import sleep

from raspberry_py.gpio.displays import Lcd1602
from raspberry_py.utils import get_cpu_temp, get_local_ip_address


def main():

    lcd = Lcd1602.init_lcd(2, None)

    try:
        while True:
            lcd.set_cursor(0, 0)  # set cursor position
            lcd.message(f'CPU:  {get_cpu_temp()}\n')
            lcd.message(datetime.now().strftime('    %H:%M:%S'))
            sleep(5)
            lcd.clear()
            lcd.message(f'Local IP:\n{get_local_ip_address()}')
            sleep(5)
            lcd.clear()
    except KeyboardInterrupt:
        pass

    lcd.clear()
    lcd.pcf8574.destroy()


if __name__ == '__main__':
    main()
