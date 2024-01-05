[Home](index.md) > Ubuntu Operating System
* Content
{:toc}

# Ubuntu Operating System
Raspberry Pi now provides a 64-bit Debian-based operating system via the Raspberry Pi Imager. However, in my experience,
this operating system can be non-performant, particularly with regard to PyCharm, which is my preferred Python 
integrated development environment (IDE). I've found that a combination of Ubuntu Server and Xubuntu Desktop performs
quite well. The installation is a bit more complicated than the standard Raspberry Pi operating system, and the steps
are listed below.

# Base Operating System
1. Download 
   [Ubuntu Server 22.04.2 64-bit LTS for Raspberry Pi](https://old-releases.ubuntu.com/releases/22.04/ubuntu-22.04.2-preinstalled-server-arm64+raspi.img.xz). 
   At the time of writing, this was the most recent LTS version that was distributed with version 5 of the Linux kernel.
   This is important because the raspberry-py package uses the [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) package, 
   which is based on a legacy GPIO interface that was removed from more recent Ubuntu Server versions that come with 
   version 6 of the Linux kernel. A compatibility shim exists in the form of
   [rpi-lgpio](https://pypi.org/project/rpi-lgpio/); however, I've had trouble installing this shim into Python virtual 
   environments. In the end, until things change, Ubuntu version 22.04.2 and version 5 of the Linux kernel will work.  
2. Install and start the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
3. Select the Ubuntu image that you downloaded and write the image to the micro-SD card. Be sure to configure WiFi and 
   SSH services on the image if needed.
4. Boot the Raspberry Pi on the micro-SD card and log in.
5. Upgrade and install a few dependencies, general tools and applications, and the Xubuntu desktop environment:
   ```shell
   sudo apt update
   sudo apt upgrade
   sudo apt install xubuntu-core emacs firefox python3-venv raspi-config i2c-tools apache2 net-tools
   sudo systemctl reboot
   ```
   The Pi should reboot into the Xubuntu desktop environment. Log in.

# GitHub
1. Run `ssh-keygen` and upload the content of `~/.ssh/id_rsa.pub` to [GitHub](https://github.com/settings/ssh/new).
2. Clone the [raspberry-py](https://github.com/MatthewGerber/raspberry-py) repository with 
   `git clone git@github.com:MatthewGerber/raspberry-py.git`.

# PyCharm
1. Download the community version [here](https://www.jetbrains.com/pycharm/download). Be sure to download the Linux ARM
   distribution, which is required for the Pi.
2. Extract the archive and move the extracted directory to `/opt/`
3. Add the PyCharm `bin` directory to your `PATH` in `.bashrc`.
4. Start PyCharm and open the raspberry-py repository.

# I2C Interface
1. Run `raspi-config` and enable the I2C interface.
2. Run `i2cdetect -y 1` to confirm. A blank I2C readout will be displayed if no I2C peripherals are connected.

# GPIO
By default, Ubuntu does not give the user permission to interact with the GPIO pins of the Raspberry Pi. To grant GPIO 
permissions when the Raspberry Pi boots:

1. Edit `/etc/udev/rules.d/99-gpiomem.rules` as follows to assign all `gpio*` device to the `dialout` group, which the 
user is a member of by default:
   ```
   KERNEL=="gpio*", OWNER="root", GROUP="dialout"
   ```
2. Reboot for the new permissions to take effect.

# Raspberry Pi Video Camera
1. Modify boot config:  `sudo emacs /boot/firmware/config.txt` and add `start_x=1` and `gpu_mem=256` at the end.
2. Enable camera:  `sudo apt install raspi-config`, then `raspi-config`, then enable the camera.
3. Give permission:  `sudo usermod -a -G video ubuntu`
4. Restart:  `sudo shutdown -r now`
5. Test:  `raspistill -o test.jpg`

# mjpg-streamer
The `mjpg-streamer` utility is an efficient way to stream video from various input devices (e.g., Raspberry Pi camera 
module or USB webcam) to various output devices (e.g., web browser). Install as follows:
```shell
sudo apt install libjpeg-turbo8-dev imagemagick ffmpeg libv4l-dev cmake libgphoto2-dev libopencv-dev libsdl-dev libprotobuf-c-dev v4l-utils
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

# OctoPrint
1. Install OctoPrint [manually](https://octoprint.org/download/#installing-manually) and start the server:
   ```shell
   cd ~
   python3.10 -m venv OctoPrint
   . OctoPrint/bin/activate
   pip install -U pip
   pip install OctoPrint
   octoprint serve
   ``` 
2. To start OctoPrint on boot:  `crontab -e` and add `@reboot /path/to/OctoPrint/run.sh`. Then create the `run.sh`
   file as follows:
   ```shell
   #!/bin/sh
   cd /path/to/OctoPrint
   . ./bin/activate
   /usr/bin/nohup octoprint serve --port 5001 &
   ```
   I use port 5001 above (different from the OctoPrint default of 5000) because the Flask REST server that is part of 
   the present raspberry-py package uses port 5000.  
3. The following script will toggle the mjpeg-streamer on and off:
   ```shell
   #!/bin/sh
   cd /home/matthewgerber/Repos/mjpg-streamer/mjpg-streamer-experimental
   if test -f streamer.pid; then
       kill `cat streamer.pid`
       rm streamer.pid
   else
       nohup ./mjpg_streamer -i "input_uvc.so -fps 30 -r 1280x720 -q 100" -o "./output_http.so -p 8081 -w ./www" &
       echo "$!" > streamer.pid
   fi
   ```
   I use port 8081 above because the Apache server used as part of the present raspberry-py package uses port 8080.
   Once the stream begins, you should be able to use the following values within OctoPrint's webcam setup:

   * Stream URL:  http://XXXX:8081/?action=stream
   * Snapshot URL:  http://XXXX:8081/?action=snapshot
   
   In the above, `XXXX` is the IP address of the Pi system. For greater convenience, add the `CMD exec` plugin to 
   OctoPrint and use the full path to the shell script as the command. This will allow you to toggle the webcam from 
   the OctoPrint web interface.

# References
* [Setting up OctoPrint on a Raspberry Pi running Raspberry Pi OS (Debian)](https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspberry-pi-os-debian/2337#optional-webcam-9)
