from datetime import datetime
from time import sleep

from raspberry_py.gpio.displays import Lcd1602
from raspberry_py.utils import get_cpu_temp


def main():

    lcd = Lcd1602(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], pcf8574_address=Lcd1602.Pcf8574.PCF8574_ADDRESS)
    lcd.begin(2)  # set number of LCD lines

    try:
        while True:
            lcd.set_cursor(0, 0)  # set cursor position
            lcd.message(f'CPU:  {get_cpu_temp()}\n')
            lcd.message(datetime.now().strftime('    %H:%M:%S'))
            sleep(0.5)
    except KeyboardInterrupt:
        pass

    lcd.clear()
    lcd.pcf8574.destroy()


if __name__ == '__main__':
    main()
