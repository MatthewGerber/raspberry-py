#!/bin/sh

# to run this upon startup, add the following via `sudo crontab -e`:
# 
#  @reboot /home/ubuntu/Repos/raspberry-py/src/raspberry_py/rest/examples/freenove_smart_car/startup.sh
#

cd /home/ubuntu/Repos/raspberry-py || exit
. venv/bin/activate
cd src/raspberry_py/rest/examples || exit
flask --app freenove_smart_car.freenove_smart_car run --host 0.0.0.0 --port 5050
