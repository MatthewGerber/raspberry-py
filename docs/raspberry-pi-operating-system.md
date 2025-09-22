[Home](index.md) > Raspberry Pi Operating System
* Content
{:toc}

# Raspberry Pi Operating System
Raspberry Pi now provides a 64-bit Debian-based operating system (OS) via the Raspberry Pi Imager. The OS is quite 
good, though for some uses [Ubuntu](ubuntu-operating-system.md) seems to work equally well if not better.

# Base Operating System
1. Install and start the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Select the latest 64-bit Raspberry Pi image and write the image to the micro-SD card. Be sure to configure WiFi and 
   SSH services on the image if needed.
3. Boot the Raspberry Pi on the micro-SD card and log in.
4. Upgrade and install a few dependencies, general tools, and applications:
   ```shell
   sudo apt update
   sudo apt upgrade
   sudo apt install emacs apache2
   sudo systemctl reboot
   ```
   The Pi should reboot. Log in.
5. If you're planning to use [OctoPrint](octoprint.md) for 3D printing, also install the following packages:
   ```shell
   sudo apt install libjpeg62-turbo-dev imagemagick ffmpeg libv4l-dev cmake libgphoto2-dev libopencv-dev libsdl1.2-dev libprotobuf-c-dev v4l-utils
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

# Raspberry Pi Video Camera
1. Modify boot config:  `sudo emacs /boot/firmware/config.txt` and add `start_x=1` and `gpu_mem=256` at the end.
2. Enable camera:  Run `raspi-config` and enable the camera.
3. Restart:  `sudo shutdown -r now`
4. Test:  `raspistill -o test.jpg`

# VNC
Run `raspi-config` and enable VNC under interface options. Then open an SSH tunnel to the Pi:
```
ssh -L 59000:localhost:5900 -l USER IP
```
In the above, `USER` is a local account on the Pi, and `IP` is the address of the Pi. Finally, open a VNC client on your 
remote machine (e.g., RealVNC) and open a connection to `localhost:59000`. Log in with the local account on the Pi.

# Mount Google Drive
See [here](mount-google-drive.pdf).

# IGT Mania
See [here](itg-mania.md).