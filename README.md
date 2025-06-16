# daq_tools
common interface for data acquisition hardware control 

## Installation

On linux make sure you're part of group dialout:
```bash
groups | grep dialout
```

If not add yourself to group:
```bash
sudo usermod -aG dialout $USER
```

Reboot to make sure changes are applied

### Dependencies

Labjack exodriver

```bash
sudo apt install build-essential libusb-1.0-0-dev
git clone https://github.com/labjack/exodriver.git
cd exodriver/
sudo ./install.sh
```

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

## Example

Print available boards and serial ports

```python
from daq_tools import Arduino_DAQ
print(Arduino_DAQ.list_boards())
```

Turn on and off digital pin 
```python
import time
from daq_tools import Arduino_DAQ

daq = Arduino_DAQ('/dev/ttyUSB0')
daq.digital_write(11, True)
time.sleep(1)
daq.digital_write(11, False)
daq.close()
```

Alternatively you can use a context manager
```python
import time
from daq_tools import Arduino_DAQ

with Arduino_DAQ('/dev/ttyUSB0') as daq:
    daq.digital_write(11, True)
    time.sleep(1)
    daq.digital_write(11, False)
```