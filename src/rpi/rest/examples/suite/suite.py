from flask_cors import CORS
from smbus2 import SMBus

from rpi.gpio import setup, CkPin
from rpi.gpio.adc import ADS7830
from rpi.gpio.lights import LED
from rpi.gpio.motors import DcMotor, Servo
from rpi.gpio.sensors import Thermistor, Photoresistor
from rpi.gpio.sounds import ActiveBuzzer
from rpi.rest.application import app

# allow cross-site access from an html front-end
CORS(app)

# set up gpio
setup()

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
    enable_pin=CkPin.GPIO22,
    in_1_pin=CkPin.GPIO27,
    in_2_pin=CkPin.GPIO17,
    speed=0
)
motor.id = 'motor-1'
app.add_component(motor)

led = LED(output_pin=CkPin.GPIO4)
led.id = 'led-1'
app.add_component(led)

servo = Servo(
    signal_pin=CkPin.GPIO18,
    min_pwm_high_ms=0.5,
    max_pwm_high_ms=2.5,
    pwm_high_offset_ms=0.0,
    min_degree=0.0,
    max_degree=180.0,
    degrees=0.0
)
servo.id = 'servo-1'
app.add_component(servo)

# stepper = Stepper(
#     poles=32,
#     output_rotor_ratio=1/64.0,
#     driver_pin_1=CkPin.GPIO19,
#     driver_pin_2=CkPin.GPIO23,
#     driver_pin_3=CkPin.GPIO24,
#     driver_pin_4=CkPin.GPIO25
# )
# stepper.id = 'stepper-1'
# app.add_component(stepper)
#
photoresistor = Photoresistor(
    adc=adc,
    channel=photoresistor_ad_channel
)
photoresistor.id = 'photoresistor-1'
app.add_component(photoresistor)

thermistor = Thermistor(
    adc=adc,
    channel=thermistor_ad_channel
)
thermistor.id = 'thermistor-1'
app.add_component(thermistor)
#
# hygrothermograph = Hygrothermograph(
#
# )
# hygrothermograph.id = 'hygrothermograph-id'
# app.add_component(hygrothermograph)
#
# infrared_motion_sensor = InfraredMotionSensor(
#
# )
# infrared_motion_sensor.id = 'infrared_motion_sensor-1'
# app.add_component(infrared_motion_sensor)
#
# ultrasonic_range_finder = UltrasonicRangeFinder(
#
# )
# ultrasonic_range_finder.id = 'ultrasonic_range_finder-1'
# app.add_component(ultrasonic_range_finder)
#
active_buzzer = ActiveBuzzer(
    output_pin=CkPin.GPIO5
)
active_buzzer.id = 'active_buzzer-1'
app.add_component(active_buzzer)
#
# passive_buzzer = PassiveBuzzer(
#
# )
# passive_buzzer.id = 'passive_buzzer-1'
# app.add_component(passive_buzzer)
