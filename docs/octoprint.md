[Home](index.md) > OctoPrint
* Content
{:toc}

# OctoPrint
This page describes steps for configuring OctoPrint on the Pi and using mjpg-streamer to stream video from a webcam to
OctoPrint for the purposes of remote monitoring and recording timelapse videos of print jobs.

# Install mjpg-streamer
The mjpg-streamer utility is an efficient way to stream video from various input devices (e.g., Raspberry Pi camera 
module or USB webcam) to various output devices (e.g., web browser). General operating system dependencies differ 
between [Rasberry Pi OS](raspberry-pi-operating-system.md) and [Ubuntu OS](ubuntu-operating-system.md). See the note 
"If you're planning to use OctoPrint for 3D printing..." in these pages for dependencies. Install the rest of 
mjpeg-streamer as follows:
```shell
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

# Install OctoPrint
1. Install OctoPrint [manually](https://octoprint.org/download/#installing-manually) and start the server:
   ```shell
   cd ~
   python3 -m venv OctoPrint
   . OctoPrint/bin/activate
   pip install -U pip
   pip install OctoPrint
   octoprint serve
   ``` 
2. To start OctoPrint on boot:  `crontab -e` and add `@reboot /path/to/OctoPrint/run.sh`. Then create the `run.sh` file 
   as follows:
   ```shell
   #!/bin/sh
   cd /path/to/OctoPrint
   . ./bin/activate
   /usr/bin/nohup octoprint serve --port 5001 &
   ```
   I use port 5001 above (different from the OctoPrint default of 5000) because the Flask REST server that is part of 
   the present raspberry-py package uses port 5000. In the above, be sure to replace `/path/to/` as appropriate.  
3. The following script, which you can save as `webcam.sh`, will toggle the mjpeg-streamer on and off:
   ```shell
   #!/bin/sh
   cd /path/to/mjpg-streamer/mjpg-streamer-experimental
   if test -f streamer.pid; then
       kill `cat streamer.pid`
       rm streamer.pid
   else
       nohup ./mjpg_streamer -i "input_uvc.so -fps 30 -r 1280x720 -q 100" -o "./output_http.so -p 8081 -w ./www" &
       echo "$!" > streamer.pid
   fi
   ```
   In the above, be sure to replace `/path/to/` as appropriate. I use port 8081 above because the Apache server used as 
   part of the present raspberry-py package uses port 8080. Once the stream begins, you should be able to use the 
   following values within OctoPrint's webcam setup:

   * Stream URL:  http://XXXX:8081/?action=stream
   * Snapshot URL:  http://XXXX:8081/?action=snapshot
   
   In the above, `XXXX` is the IP address of the Pi system. For greater convenience, add the `CMD exec` plugin to 
   OctoPrint and use the full path to the shell script as the command. This will allow you to toggle the webcam from 
   the OctoPrint web interface.

# References
* [Setting up OctoPrint on a Raspberry Pi running Raspberry Pi OS (Debian)](https://community.octoprint.org/t/setting-up-octoprint-on-a-raspberry-pi-running-raspberry-pi-os-debian/2337#optional-webcam-9)