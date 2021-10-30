import smbus2


class ADCDevice:

    def __init__(self):
        self.cmd = 0
        self.address = 0
        self.bus = smbus2.SMBus(1)

    def detect_i2c(self, address):
        try:
            self.bus.write_byte(address, 0)
            print(f'Found device in address 0x{address}')
            return True
        except:
            print(f'Not found device in address 0x{address}')
            return False

    def close(self):
        self.bus.close()


class PCF8591(ADCDevice):

    def __init__(self):
        super(PCF8591, self).__init__()
        self.cmd = 0x40     # The default command for PCF8591 is 0x40.
        self.address = 0x48  # 0x48 is the default i2c address for PCF8591 Module.

    def analog_read(self, chn):  # PCF8591 has 4 ADC input pins, chn:0,1,2,3
        value = self.bus.read_byte_data(self.address, self.cmd+chn)
        value = self.bus.read_byte_data(self.address, self.cmd+chn)
        return value

    def analog_write(self, address, cmd, value): # write DAC value
        self.bus.write_byte_data(address, cmd, value)


class ADS7830(ADCDevice):

    def __init__(self):

        super().__init__()

        self.cmd = 0x84
        self.address = 0x4b  # 0x4b is the default i2c address for ADS7830 Module.

    def analog_read(self, chn):  # ADS7830 has 8 ADC input pins, chn:0,1,2,3,4,5,6,7
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value
