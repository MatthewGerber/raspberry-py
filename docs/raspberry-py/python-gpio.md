[Home](../index.md) > Python Interface for GPIO Circuits

# Introduction
Whereas the lower-level [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) package deals with GPIO input/output pins and 
high/low values, the present package deals with LEDs that are on or off, button switches that are pressed or not, and so 
on. These abstractions, in combination with an event-driven framework, allow the developer to express the intended 
circuit behavior more naturally compared with lower-level interfaces. 

# Examples
For example, a blinking LED program is written as follows:
```
import time
from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.lights import LED

setup()

# create an led on output pin 11
led = LED(output_pin=11)

# set on for 1 second then off
led.turn_on()
time.sleep(1)
led.turn_off()

cleanup()
```
A button-switched LED is shown below:

```
import time

from raspberry_py.gpio import setup, cleanup
from raspberry_py.gpio.lights import LED
from raspberry_py.gpio.controls import TwoPoleButton

setup()

# create an led on output pin 11
led = LED(output_pin=11)

# create a button on input pin 12
button = TwoPoleButton(input_pin=12, bounce_time_ms=300)

# turn the led on when the button is pressed
button.event(lambda s: led.turn_on() if s.pressed else led.turn_off())

print('You have 20 seconds to press the button...')
time.sleep(20)

cleanup()
```

Buzzing LED bar with push button (click to watch; Python code [here](https://github.com/MatthewGerber/raspberry-py/blob/main/src/raspberry_py/gpio/examples/buzzing_led_bar_with_button.py)):

{% include youtubePlayer.html id="e6PrM2QVSA4" %}

Python code for these and other examples can be found [here](https://github.com/MatthewGerber/raspberry-py/tree/main/src/raspberry_py/gpio/examples).
