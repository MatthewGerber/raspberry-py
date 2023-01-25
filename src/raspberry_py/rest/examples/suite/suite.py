from smbus2 import SMBus

from raspberry_py.gpio import CkPin
from raspberry_py.gpio.adc import ADS7830
from raspberry_py.gpio.lights import LED
from raspberry_py.gpio.motors import DcMotor, Servo, DcMotorDriverL293D, ServoDriverSoftwarePWM
from raspberry_py.gpio.sensors import Thermistor, Photoresistor, UltrasonicRangeFinder
from raspberry_py.gpio.sounds import ActiveBuzzer
from raspberry_py.rest.application import app

# some components require a/d conversion
thermistor_ad_channel = 0
photoresistor_ad_channel = 1
adc = ADS7830(
    input_voltage=3.3,
    bus=SMBus('/dev/i2c-1'),
    address=ADS7830.ADDRESS,
    command=ADS7830.COMMAND,
    channel_rescaled_range={
        thermistor_ad_channel: None,
        photoresistor_ad_channel: (100, 0)
    }
)

motor = DcMotor(
    driver=DcMotorDriverL293D(
        enable_pin=CkPin.GPIO22,
        in_1_pin=CkPin.GPIO27,
        in_2_pin=CkPin.GPIO17
    ),
    speed=0
)
motor.id = 'motor-1'
app.add_component(motor, True)

led = LED(output_pin=CkPin.GPIO4)
led.id = 'led-1'
app.add_component(led, True)

servo = Servo(
    driver=ServoDriverSoftwarePWM(
        signal_pin=CkPin.GPIO18,
        min_pwm_high_ms=0.5,
        max_pwm_high_ms=2.5,
        pwm_high_offset_ms=0.0,
        min_degree=0.0,
        max_degree=180.0
    ),
    degrees=0.0,
    min_degree=0.0,
    max_degree=180.0
)
servo.id = 'servo-1'
app.add_component(servo, True)

photoresistor = Photoresistor(
    adc=adc,
    channel=photoresistor_ad_channel
)
photoresistor.id = 'photoresistor-1'
app.add_component(photoresistor, True)

thermistor = Thermistor(
    adc=adc,
    channel=thermistor_ad_channel
)
thermistor.id = 'thermistor-1'
app.add_component(thermistor, True)

ultrasonic_range_finder = UltrasonicRangeFinder(
    trigger_pin=CkPin.GPIO23,
    echo_pin=CkPin.GPIO24,
    measurements_per_second=2
)
ultrasonic_range_finder.id = 'ultrasonic_range_finder-1'
app.add_component(ultrasonic_range_finder, True)

active_buzzer = ActiveBuzzer(
    output_pin=CkPin.GPIO5
)
active_buzzer.id = 'active_buzzer-1'
app.add_component(active_buzzer, True)
