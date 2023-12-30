Home
* Content
{:toc}

# Features

## Python Interface for GPIO Circuits
This package provides two related capabilities. [First](python-gpio.md), it provides a high-level, event-driven Python 
interface for GPIO circuits running on the Raspberry Pi. Sensors, motors, LEDs, switches, and many other components are 
covered.

{% include youtubePlayer.html id="e6PrM2QVSA4" %}

## Remote Control of GPIO Circuits via REST/HTML/JavaScript
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
python -m venv venv
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
integrated development environment (IDE). I've found that a combination of Ubuntu Service and Xubuntu Desktop performs
quite well. The installation is a bit more complicated than the standard Raspberry Pi operating system, and the steps
are listed below.

## Base Operating System

1. Install and start the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Select the latest Ubuntu Server 64-bit OS and write the image to the micro-SD card. Be sure to configure WiFi and SSH
   services on the image.
3. Boot the Raspberry Pi and log in.
4. `sudo apt update && sudo apt upgrade`
5. `sudo systemctl reboot`
6. `sudo apt install xubuntu-core emacs firefox gcc python3-dev python3-venv raspi-config i2c-tools apache2 net-tools swig`
7. `sudo systemctl reboot`
8. `ssh-keygen` and then upload the key to GitHub if needed.

## PyCharm
1. Download [here](https://www.jetbrains.com/pycharm/download).
2. Extract the archive and move the PyCharm directory to `/opt/`
3. Add the PyCharm `bin` directory to your `PATH` in `.bashrc`.

## I2C Interface
1. Run `raspi-config` and enable the I2C interface.
2. Run `i2cdetect -y 1` to confirm. A blank I2C readout will be displayed if no I2C peripherals are connected.

## GPIO
By default, Ubuntu does not give the user permission to interact with the GPIO pins of the Raspberry Pi. To grant GPIO 
permissions when the Raspberry Pi boots:

1. Edit `/etc/udev/rules.d/99-gpiomem.rules` as follows to assign all `gpio*` device to the `dialout` group, which the 
user is a member of by default:
   ```
   KERNEL=="gpio*", OWNER="root", GROUP="dialout"
   ```
2. Reboot for the new permissions to take effect.

## Raspberry Pi Video Camera
1. Modify boot config:  `sudo emacs /boot/firmware/config.txt` and add `start_x=1` and `gpu_mem=256` at the end.
2. Enable camera:  `sudo apt install raspi-config`, then `raspi-config`, then enable the camera.
3. Give permission:  `sudo usermod -a -G video ubuntu`
4. Restart:  `sudo shutdown -r now`
5. Test:  `raspistill -o test.jpg`

## mjpg_streamer
The `mjpg_streamer` utility is an efficient way to stream video from various input devices (e.g., Raspberry Pi camera 
module or USB webcam) to various output devices (e.g., web browser). Install as follows:
```shell
sudo apt install subversion libjpeg-turbo8-dev imagemagick ffmpeg libv4l-dev cmake libgphoto2-dev libopencv-dev libsdl-dev libprotobuf-c-dev v4l-utils
git clone https://github.com/jacksonliam/mjpg-streamer.git
cd mjpg-streamer/mjpg-streamer-experimental/
export LD_LIBRARY_PATH=.
make
```
List connected video devices:
```
v4l2-ctl --list-devices

mmal service 16.1 (platform:bcm2835-v4l2):
	/dev/video2

WEB CAM: WEB CAM (usb-0000:01:00.0-1.1):
	/dev/video0
	/dev/video1
	/dev/media0
```
The first (connected to `/dev/video2`) is 
[a Raspberry Pi camera module](https://www.raspberrypi.com/products/camera-module-v2/). The second (connected to 
`/dev/video0`) is [a USB webcam](https://www.amazon.com/dp/B087M3BVP9).

To stream the Raspberry Pi camera module:
```
./mjpg_streamer -i "input_uvc.so -d /dev/video2 -fps 15" -o "output_http.so -p 8081 -w ./www"
```
Alternatively, to stream the USB webcam:
```
./mjpg_streamer -i "input_uvc.so -d /dev/video0 -fps 15" -o "./output_http.so -p 8081 -w ./www"
```
In both of the above:
* `-d /dev/video*` selects the video input device.
* `-f 15` runs the camera at 15 frames per second.
* `-p 8081` serves the MJPG stream on port 8081 of all IP interfaces.
* `-w ./www` points the streamer at the `www` directory.

Once the streamer is up and running, navigate to `http://xxxx:8081/` for an overview or 
`http://xxxx:8081/?action=stream` for a dedicated stream (where `xxxx` is the IP address of the Raspberry Pi). 

It can happen that a process is holding a `/dev/video*` device, which prevents your camera from connecting. List video
devices:
```
sudo fuser /dev/video*
/dev/video0:          1418m
```
Dig a bit more:
```
ps aux | grep 1418
root        1418  0.0  0.8 304784 65344 ?        Sl   20:36   0:02 ...
```
Then kill the process if you wish:
```
sudo kill 1418
```

References:
* [Setting up OctoPrint on a Raspberry Pi running Raspberry Pi OS (Debian)](https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspberry-pi-os-debian/2337#optional-webcam-9)