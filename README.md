# rpi
Raspberry Pi

## Examples
1. Blinking LED

## Installation on Ubuntu
On an Ubuntu 20.04 Server LTS 64-bit OS, enable GPIO device permissions on boot:
1. Edit `sudo emacs /etc/udev/rules.d/99-gpiomem.rules` as follows:
```
KERNEL=="gpiomem", OWNER="root", GROUP="dialout"
```
2. Test the permissions:  `sudo udevadm trigger /dev/gpiomem`
