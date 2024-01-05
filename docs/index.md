Home
* Content
{:toc}

# Python Interface for GPIO Circuits
This package provides two related capabilities. [First](python-gpio.md), it provides a high-level, event-driven Python 
interface for GPIO circuits running on the Raspberry Pi. Sensors, motors, LEDs, switches, and many other components are 
covered.

{% include youtubePlayer.html id="e6PrM2QVSA4" %}

# Remote Control of GPIO Circuits via REST/HTML/JavaScript
[Second](remote-gpio.md), this package enables remote control of GPIO circuits via REST APIs invoked from 
HTML/JavaScript front-ends. Want to control your circuit remotely from your phone? Look no further. This package 
auto-generates HTML/JavaScript for GPIO circuits based on [Material Design for Bootstrap](https://mdbootstrap.com). 
These HTML/JavaScript elements can be embedded in full web pages for remote control of the circuit. The remote control 
screen for the [Freenove Smart Car](smart-car.md) is shown below:

![freenove-smart-car](smart-car.png)

As another example, consider 
[the 3D-printed robotic arm](https://matthewgerber.github.io/raspberry-py/smart-car.html#advanced-robotic-arm) that I 
designed for the car:

<iframe src="https://gmail3021534.autodesk360.com/shares/public/SH35dfcQT936092f0e4344f64dd3dcf58a6f?mode=embed" width="800" height="600" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true"  frameborder="0"></iframe>

Additional CAD parts that I have designed are listed [here](cad-parts.md). 

# Use and Development
The `raspberry-py` package can be consumed in two ways:

1. Add `raspberry-py` to a project as a PyPI dependency. This is the best approach if you only want to use the 
functionality provided by `raspberry-py`. The `raspberry-py` package is available 
[here](https://pypi.org/project/raspberry-py/), and an example of adding the package dependency is provided
[here](https://github.com/MatthewGerber/raspberry-py-dependency-example).
2. [Fork](https://github.com/MatthewGerber/raspberry-py/fork) the present repository and then install it locally. This 
is the best approach if you want to enhance and/or fix the functionality provided by `raspberry-py`. In the following, 
`XXXX` is the user account into which the repository is forked:
```shell
git clone git@github.com:XXXX/raspberry-py.git
cd raspberry-py
python3.10 -m venv venv
. venv/bin/activate
pip install -U pip
pip install -e .
```
From here, you can push back to your fork and submit a pull request to the original if desired.

# CAD Parts
I have designed a range of parts for integration with the Raspberry Pi. See [here](cad-parts.md). 

# Ubuntu Operating System
Raspberry Pi now provides a 64-bit Debian-based operating system via the Raspberry Pi Imager. However, in my experience,
this operating system can be non-performant, particularly with regard to PyCharm, which is my preferred Python 
integrated development environment (IDE). I've found that a combination of Ubuntu Server and Xubuntu Desktop performs
quite well. The installation is a bit more complicated than the standard Raspberry Pi operating system, and the steps
are listed [here](ubuntu-operating-system.md).