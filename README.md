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

## Example

```python

from daq_tools import Arduino_DAQ
daq = Arduino_DAQ()
```