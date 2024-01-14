[Home](index.md) > Ubuntu Operating System
* Content
{:toc}

# Ubuntu Operating System
Raspberry Pi now provides a 64-bit Debian-based operating system (OS) via the Raspberry Pi Imager. However, in my 
experience, this OS can be non-performant, particularly with regard to PyCharm, which is my preferred Python 
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
6. If you're planning to use [OctoPrint](octoprint.md) for 3D printing, also install the following packages:
   ```shell
   sudo apt install libjpeg-turbo8-dev imagemagick ffmpeg libv4l-dev cmake libgphoto2-dev libopencv-dev libsdl-dev libprotobuf-c-dev v4l-utils
   ```

# GitHub
1. Run `ssh-keygen` and upload the content of `~/.ssh/id_rsa.pub` to [GitHub](https://github.com/settings/ssh/new).
2. Clone the [raspberry-py](https://github.com/MatthewGerber/raspberry-py) repository with 
   `git clone git@github.com:MatthewGerber/raspberry-py.git`.

# PyCharm
1. Download the community version [here](https://www.jetbrains.com/pycharm/download). Be sure to download the Linux ARM
   distribution, which is required for the Pi.
2. Extract the archive and move the extracted directory to `/opt/`
3. Add the PyCharm `bin` directory to your `PATH` in `~/.bashrc`.
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
2. Enable camera:  Run `raspi-config` and enable the camera.
3. Give permission:  `sudo usermod -a -G video ubuntu`
4. Restart:  `sudo shutdown -r now`
5. Test:  `raspistill -o test.jpg`
