#!/bin/sh

# to run this upon startup, add the following via `sudo crontab -e`:
# 
#  @reboot /home/ubuntu/Repos/rpi/src/rpi/rest/examples/freenove_smart_car/startup.sh
#

cd /home/ubuntu/Repos/rpi || exit
. venv/bin/activate
cd src/rpi/rest/examples || exit
flask --app freenove_smart_car.freenove_smart_car run --host 0.0.0.0
