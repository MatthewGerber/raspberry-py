# [Freenove 4WD Smart Car](https://www.amazon.com/Freenove-Raspberry-Tracking-Avoidance-Ultrasonic/dp/B07YD2LT9D):

UNDER CONSTRUCTION

![smart-car](smart-car.png)

# Enabling the LED Strip

Some resources:
* https://pypi.org/project/rpi-ws281x/
* https://unix.stackexchange.com/questions/475800/non-root-read-access-to-dev-mem-by-kmem-group-members-fails
* https://unix.stackexchange.com/questions/303423/unset-setcap-additional-capabilities-on-excutable

```
sudo chmod g+w /dev/mem
sudo usermod -a -G kmem ubuntu 
```

```
which python
```

```
sudo setcap cap_sys_rawio+ep /usr/bin/python3.9
```

```
sudo shutdown -r now
```