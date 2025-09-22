
Install ITGmania:

```shell
sudo apt install nasm yasm libxrandr-dev libxtst-dev libxinerama-dev libudev-dev libgdk-pixbuf-2.0-0 libgl1 libglvnd0 libgtk-3-0 libusb-0.1-4 libxinerama1 libxtst6
git clone --recurse-submodules git@github.com:itgmania/itgmania.git
cd itgmania/Build
cmake -G 'Unix Makefiles' -DCMAKE_BUILD_TYPE=Release -DWITH_MINIMAID=OFF .. && cmake ..
cd ../
cmake -B Build
cd Build
sudo make install
```