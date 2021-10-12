# RPI
This package provides a high-level, event-driven interface for GPIO circuits running on the Raspberry Pi. Whereas
the lower-level [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) package deals with GPIO input/output pins and high/low
values, the RPI package deals with LEDs that are on or off, button switches that are pressed or not, and so on. These
abstractions, in combination with an event-driven framework, allow the developer to express the intended circuit 
behavior more naturally compared with lower-level interfaces. For example, a blinking LED program is written as follows:
```python
import time
from rpi.gpio import setup, cleanup
from rpi.gpio.lights import LED

setup()

# create an led on output pin 11
led = LED(output_pin=11)

# set on for 1 second then off
led.set(LED.State(on=True))
time.sleep(1)
led.set(LED.State(on=False))

cleanup()
```
A more complex example using a button-switched LED is shown below:
```python
import time
from rpi.gpio import setup, cleanup, Clock
from rpi.gpio.lights import LED
from rpi.gpio.switches import TwoPoleButton

setup()

# create an led on output pin 11
led = LED(output_pin=11)

# create a button on input pin 12
button = TwoPoleButton(input_pin=12)

# create a clock that ticks as quickly as possible. this will be the event source for updating the button's state.
clock = Clock(tick_interval_seconds=None)

# update the button state each clock tick
clock.add_listener(
    trigger=lambda clock_state: True,
    event=lambda: button.update()
)

# turn the led on when the button is pressed
button.add_listener(
    trigger=lambda button_state: True,
    event=lambda: led.set(LED.State(on=button.get().pressed))
)

# start clock and run for 10 seconds
clock.start()
print('You have 20 seconds to press the button...')
time.sleep(20)
clock.stop()

cleanup()
```

Other examples can be found [here](src/rpi/gpio/examples).

## Installation
This package has been developed using the Ubuntu installation described 
[here](https://matthewgerber.github.io/rlai/raspberry_pi.html). By default, Ubuntu does not give the user permission
to interact with the GPIO pins of the Raspberry Pi. To grant GPIO permissions when the Raspberry Pi boots:
1. Edit `/etc/udev/rules.d/99-gpiomem.rules` as follows to assign the `gpiomem` device to the `dialout` 
group, which the user is a member of by default:
```
KERNEL=="gpiomem", OWNER="root", GROUP="dialout"
```
2. Test the permissions:  `sudo udevadm trigger /dev/gpiomem`
