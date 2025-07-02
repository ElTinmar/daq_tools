# daq_tools
common interface for data acquisition hardware control 

## Installation

### Conda

```bash
git clone https://github.com/ElTinmar/daq_tools.git
cd daq_tools
conda env create -f daq_tools.yml
conda activate daq_tools
```

### Pip

```bash
pip install git+https://github.com/ElTinmar/daq_tools.git@main
```

## Dependencies

On linux make sure you're part of group dialout:
```bash
groups | grep dialout
```

If not add yourself to group:
```bash
sudo usermod -aG dialout $USER
```

Reboot to make sure changes are applied

### Labjack exodriver

```bash
sudo apt install build-essential libusb-1.0-0-dev
git clone https://github.com/labjack/exodriver.git
cd exodriver/
sudo ./install.sh
```

### Load Firmata Sketch on the Arduino

Install the arduino IDE

```bash
sudo add-apt-repository universe
sudo apt install libfuse2
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="2341", GROUP="plugdev", MODE="0666"' | sudo tee /etc/udev/rules.d/99-arduino.rules
```

Get appimage here: https://github.com/arduino/arduino-ide/releases/latest

```bash
chmod +x arduino-ide_2.3.6_Linux_64bit.AppImage
./arduino-ide_2.3.6_Linux_64bit.AppImage --no-sandbox
```

The sketch is available in the Arduino IDE’s built-in examples. To open it, access the File menu, then Examples, followed by Firmata, and finally StandardFirmata.
1. Plug the USB cable into the PC.  
2. Select the appropriate board and port on the IDE.  
3. Press Upload.  

if you see the following error message

```bash
avrdude: jtagmkII_getsync(): sign-on command: status -1
```

try setting baudrate to 1200 in serial monitor and restart upload

### National Instruments

Works on Ubuntu 24.04 (couldn't get it to install on 25.04, maybe need older kernel)

```bash
conda activate daq_tools
sudo $(which python) -m nidaqmx installdriver
sudo apt install ni-hwcfg-utility
```

## Example

Print available boards and serial ports

```python
from daq_tools import Arduino_SoftTiming
print(Arduino_SoftTiming.list_boards())
```

Turn on and off digital pin

```python
import time
from daq_tools import Arduino_SoftTiming

daq = Arduino_SoftTiming('/dev/ttyUSB0')
daq.digital_write(11, True)
time.sleep(1)
daq.digital_write(11, False)
daq.close()
```

Alternatively you can use a context manager

```python
import time
from daq_tools import Arduino_SoftTiming

with Arduino_SoftTiming('/dev/ttyUSB0') as daq:
    daq.digital_write(11, True)
    time.sleep(1)
    daq.digital_write(11, False)
```
