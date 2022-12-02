from time import sleep
from typing import List

import smbus2


class Lcd1602:
    """
    LCD1602 component.
    """

    class Pcf8574:
        """
        PCF8574 chip embedded into the LCD1602.
        """

        PCF8574_ADDRESS = 0x27  # I2C address of the PCF8574 chip.
        PCF8574A_ADDRESS = 0x3F  # I2C address of the PCF8574A chip.

        def __init__(
                self,
                address: int
        ):
            """
            Initialize the chip.

            :param address: I2C address.
            """

            self.address = address

            self.bus = smbus2.SMBus(1)  # Change to 0 if running on a revision 1 Raspberry Pi.
            self.current_value = 0

        def output(
                self,
                pin: int,
                value: bool
        ):
            """
            Output a value to a pin.

            :param pin: Pin.
            :param value: Value.
            """

            byte_to_write = self.current_value

            if value:
                byte_to_write |= (1 << pin)
            else:
                byte_to_write &= ~(1 << pin)

            self.bus.write_byte(self.address, byte_to_write)
            self.current_value = byte_to_write

        def destroy(self):
            """
            Destroy the bus being used by the chip.
            """

            self.bus.close()

    # commands
    LCD_CLEAR_DISPLAY = 0x01
    LCD_RETURN_HOME = 0x02
    LCD_ENTRY_MODE_SET = 0x04
    LCD_DISPLAY_CONTROL = 0x08
    LCD_CURSOR_SHIFT = 0x10
    LCD_FUNCTION_SET = 0x20
    LCD_SET_CG_RAM_ADDRESS = 0x40
    LCD_SET_DD_RAM_ADDRESS = 0x80

    # flags for display entry mode
    LCD_ENTRY_RIGHT = 0x00
    LCD_ENTRY_LEFT = 0x02
    LCD_ENTRY_SHIFT_INCREMENT = 0x01
    LCD_ENTRY_SHIFT_DECREMENT = 0x00

    # flags for display on/off control
    LCD_DISPLAY_ON = 0x04
    LCD_DISPLAY_OFF = 0x00
    LCD_CURSOR_ON = 0x02
    LCD_CURSOR_OFF = 0x00
    LCD_BLINK_ON = 0x01
    LCD_BLINK_OFF = 0x00

    # flags for display/cursor shift
    LCD_DISPLAY_MOVE = 0x08
    LCD_CURSOR_MOVE = 0x00
    LCD_MOVE_RIGHT = 0x04
    LCD_MOVE_LEFT = 0x00

    # flags for function set
    LCD_8_BIT_MODE = 0x10
    LCD_4_BIT_MODE = 0x00
    LCD_2_LINE = 0x08
    LCD_1_LINE = 0x00
    LCD_5x10_DOTS = 0x04
    LCD_5x8_DOTS = 0x00

    def __init__(
            self,
            pin_rs: int,
            pin_e: int,
            pins_db: List[int],
            pcf8574_address: int
    ):
        """
        Initialize the LCD.

        :param pin_rs: RS pin.
        :param pin_e: E pin.
        :param pins_db: Pins.
        :param pcf8574_address: I2C address of the PCF8574 chip.
        """

        self.pin_rs = pin_rs
        self.pin_e = pin_e
        self.pins_db = pins_db
        self.pcf8574 = Lcd1602.Pcf8574(pcf8574_address)

        self.pcf8574.output(3, True)  # turn on LCD backlight

        self.num_lines = None
        self.row_offsets = None

        self.write_4_bits(0x33)  # initialization
        self.write_4_bits(0x32)  # initialization
        self.write_4_bits(0x28)  # 2 line 5x7 matrix
        self.write_4_bits(0x0C)  # turn cursor off 0x0E to enable cursor
        self.write_4_bits(0x06)  # shift cursor right

        self.display_control = self.LCD_DISPLAY_ON | self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF
        self.display_function = self.LCD_4_BIT_MODE | self.LCD_1_LINE | self.LCD_5x8_DOTS | self.LCD_2_LINE

        # Initialize to default text direction (for romance languages)
        self.display_mode = self.LCD_ENTRY_LEFT | self.LCD_ENTRY_SHIFT_DECREMENT
        self.write_4_bits(self.LCD_ENTRY_MODE_SET | self.display_mode)  # set the entry mode

        self.clear()

    def begin(self, lines):
        if lines > 1:
            self.num_lines = lines
            self.display_function |= self.LCD_2_LINE

    def home(self):
        self.write_4_bits(self.LCD_RETURN_HOME)  # set cursor position to zero
        self.delay_microseconds(3000)  # this command takes a long time!

    def clear(self):
        self.write_4_bits(self.LCD_CLEAR_DISPLAY)  # command to clear display
        self.delay_microseconds(3000)  # 3000 microsecond sleep, clearing the display takes a long time

    def set_cursor(self, col, row):

        self.row_offsets = [0x00, 0x40, 0x14, 0x54]

        if row > self.num_lines:
            row = self.num_lines - 1  # we count rows starting w/0
        self.write_4_bits(self.LCD_SET_DD_RAM_ADDRESS | (col + self.row_offsets[row]))

    def no_display(self):
        """ Turn the display off (quickly) """
        self.display_control &= ~self.LCD_DISPLAY_ON
        self.write_4_bits(self.LCD_DISPLAY_CONTROL | self.display_control)

    def display(self):
        """ Turn the display on (quickly) """
        self.display_control |= self.LCD_DISPLAY_ON
        self.write_4_bits(self.LCD_DISPLAY_CONTROL | self.display_control)

    def no_cursor(self):
        """ Turns the underline cursor off """
        self.display_control &= ~self.LCD_CURSOR_ON
        self.write_4_bits(self.LCD_DISPLAY_CONTROL | self.display_control)

    def cursor(self):
        """ Turns the underline cursor on """
        self.display_control |= self.LCD_CURSOR_ON
        self.write_4_bits(self.LCD_DISPLAY_CONTROL | self.display_control)

    def no_blink(self):
        """ Turn the blinking cursor off """
        self.display_control &= ~self.LCD_BLINK_ON
        self.write_4_bits(self.LCD_DISPLAY_CONTROL | self.display_control)

    def blink(self):
        """ Turn the blinking cursor on """
        self.display_control |= self.LCD_BLINK_ON
        self.write_4_bits(self.LCD_DISPLAY_CONTROL | self.display_control)

    def display_left(self):
        """ These commands scroll the display without changing the RAM """
        self.write_4_bits(self.LCD_CURSOR_SHIFT | self.LCD_DISPLAY_MOVE | self.LCD_MOVE_LEFT)

    def scroll_display_right(self):
        """ These commands scroll the display without changing the RAM """
        self.write_4_bits(self.LCD_CURSOR_SHIFT | self.LCD_DISPLAY_MOVE | self.LCD_MOVE_RIGHT)

    def left_to_right(self):
        """ This is for text that flows Left to Right """
        self.display_mode |= self.LCD_ENTRY_LEFT
        self.write_4_bits(self.LCD_ENTRY_MODE_SET | self.display_mode)

    def right_to_left(self):
        """ This is for text that flows Right to Left """
        self.display_mode &= ~self.LCD_ENTRY_LEFT
        self.write_4_bits(self.LCD_ENTRY_MODE_SET | self.display_mode)

    def auto_scroll(self):
        """ This will 'right justify' text from the cursor """
        self.display_mode |= self.LCD_ENTRY_SHIFT_INCREMENT
        self.write_4_bits(self.LCD_ENTRY_MODE_SET | self.display_mode)

    def no_auto_scroll(self):
        """ This will 'left justify' text from the cursor """
        self.display_mode &= ~self.LCD_ENTRY_SHIFT_INCREMENT
        self.write_4_bits(self.LCD_ENTRY_MODE_SET | self.display_mode)

    def write_4_bits(self, bits, char_mode=False):
        """ Send command to LCD """
        self.delay_microseconds(1000)  # 1000 microsecond sleep
        bits = bin(bits)[2:].zfill(8)
        self.pcf8574.output(self.pin_rs, char_mode)
        for pin in self.pins_db:
            self.pcf8574.output(pin, False)
        for i in range(4):
            if bits[i] == "1":
                self.pcf8574.output(self.pins_db[::-1][i], True)
        self.pulse_enable()
        for pin in self.pins_db:
            self.pcf8574.output(pin, False)
        for i in range(4, 8):
            if bits[i] == "1":
                self.pcf8574.output(self.pins_db[::-1][i - 4], True)
        self.pulse_enable()

    @staticmethod
    def delay_microseconds(microseconds):
        seconds = microseconds / float(1000000)  # divide microseconds by 1 million for seconds
        sleep(seconds)

    def pulse_enable(self):
        self.pcf8574.output(self.pin_e, False)
        self.delay_microseconds(1)  # 1 microsecond pause - enable pulse must be > 450ns
        self.pcf8574.output(self.pin_e, True)
        self.delay_microseconds(1)  # 1 microsecond pause - enable pulse must be > 450ns
        self.pcf8574.output(self.pin_e, False)
        self.delay_microseconds(1)  # commands need > 37us to settle

    def message(self, text):
        """ Send string to LCD. Newline wraps to second line"""
        for char in text:
            if char == '\n':
                self.write_4_bits(0xC0)  # next line
            else:
                self.write_4_bits(ord(char), True)
