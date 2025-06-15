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

```python
import time
from daq_tools import Arduino_DAQ

Arduino_DAQ.list_boards()
daq = Arduino_DAQ('/dev/ttyUSB0')
daq.digital_write(13, True)
time.sleep(1)
daq.digital_write(13, False)
```