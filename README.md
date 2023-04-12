[![PyPI version](https://badge.fury.io/py/raspberry-py.svg)](https://badge.fury.io/py/raspberry-py)

Please see the [project website](https://matthewgerber.github.io/raspberry-py/) for more information.

# Python Interface for GPIO Circuits
This package provides two related capabilities. 
[First](https://matthewgerber.github.io/raspberry-py/python-gpio.html), it provides a high-level, event-driven Python 
interface for GPIO circuits running on the Raspberry Pi. Sensors, motors, LEDs, switches, and many other components are 
covered. An example is shown below (click to watch; Python code
[here](https://github.com/MatthewGerber/raspberry-py/blob/main/src/raspberry_py/gpio/examples/buzzing_led_bar_with_button.py)):

[![Buzzing LED bar with push button](https://img.youtube.com/vi/e6PrM2QVSA4/0.jpg)](https://www.youtube.com/watch?v=e6PrM2QVSA4)

# Remote Control of GPIO Circuits via REST/HTML/JavaScript
[Second](https://matthewgerber.github.io/raspberry-py/remote-gpio.html), this package enables remote control of GPIO 
circuits via REST APIs invoked from HTML/JavaScript front-ends. Want to control your circuit remotely from your phone? 
Look no further. This package auto-generates HTML/JavaScript for GPIO circuits based on
[Material Design for Bootstrap](https://mdbootstrap.com). These HTML/JavaScript elements can be embedded in full web 
pages for remote control of the circuit. The remote control screen for the 
[Freenove Smart Car](https://matthewgerber.github.io/raspberry-py/smart-car.html) is shown below:

![freenove-smart-car](docs/smart-car.png)

The smart car is built from the same components (sensors, motors, LEDs, etc.) listed above, making development quite 
straightforward. As another example, consider 
[the 3D-printed robotic arm](https://matthewgerber.github.io/raspberry-py/smart-car.html#enhancement-robotic-arm) that I 
designed for the car.

Please see the [project website](https://matthewgerber.github.io/raspberry-py/) for more information.