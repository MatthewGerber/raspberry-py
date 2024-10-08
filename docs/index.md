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

# CAD Parts and 3D Printing
I have designed a range of parts for integration with the Raspberry Pi. See [here](cad-parts.md).

# Use and Development
Raspberry Pi now provides a 64-bit Debian-based operating system (OS) via the Raspberry Pi Imager. The OS is quite 
good, though for some uses Ubuntu seems to work equally well if not better. I've written steps for both operating 
systems [here](raspberry-pi-operating-system.md) and [here](ubuntu-operating-system.md), respectively. The following steps use [poetry](https://python-poetry.org/) for 
installation.

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
   poetry env use 3.11
   poetry install
   ```
   From here, you can push back to your fork and submit a pull request to the original if desired.

# Incrementing and Tagging Versions with Poetry
1. Begin the next prerelease number within the current prerelease phase (e.g., `0.1.0a0` → `0.1.0a1`):
   ```shell
   OLD_VERSION=$(poetry version --short)
   poetry version prerelease
   VERSION=$(poetry version --short)
   git commit -a -m "Next prerelease number:  ${OLD_VERSION} → ${VERSION}"
   git push
   ```
2. Begin the next prerelease phase (e.g., `0.1.0a1` → `0.1.0b0`):
   ```shell
   OLD_VERSION=$(poetry version --short)
   poetry version prerelease --next-phase
   VERSION=$(poetry version --short)
   git commit -a -m "Next prerelease phase:  ${OLD_VERSION} → ${VERSION}"
   git push
   ```
   The phases progress as alpha (`a`), beta (`b`), and release candidate (`rc`), each time resetting to a prerelease 
   number of 0. After `rc`, the prerelease suffix (e.g., `rc3`) is stripped, leaving the `major.minor.patch` version.
3. Release the next minor version (e.g., `0.1.0b1` → `0.1.0`):
   ```shell
   OLD_VERSION=$(poetry version --short)
   poetry version minor
   VERSION=$(poetry version --short)
   git commit -a -m "New minor release:  ${OLD_VERSION} → ${VERSION}"
   git push
   ```
4. Release the next major version (e.g., `0.1.0a0` → `2.0.0`):
   ```shell
   OLD_VERSION=$(poetry version --short)
   poetry version major
   VERSION=$(poetry version --short)
   git commit -a -m "New major release:  ${OLD_VERSION} → ${VERSION}"
   git push
   ```
5. Tag the current version:
   ```shell
   VERSION=$(poetry version --short)
   git tag -a -m "rlai v${VERSION}" "v${VERSION}"
   git push --follow-tags
   ```
6. Begin the next minor prerelease (e.g., `0.1.0` → `0.2.0a0`):
   ```shell
   OLD_VERSION=$(poetry version --short)
   poetry version preminor
   VERSION=$(poetry version --short)
   git commit -a -m "Next minor prerelease:  ${OLD_VERSION} → ${VERSION}"
   git push
   ```

# Troubleshooting
* If `poetry install` hangs when attempting to unlock the keyring, disable the keyring with the following:
  ```
  poetry config keyring.enabled false
  ```