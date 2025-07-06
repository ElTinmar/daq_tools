from typing import Dict, Type
from .core import SoftwareTimingDAQ, BoardInfo, DAQReadError, BoardType

DAQ_CONSTRUCTORS: Dict[BoardType, Type[SoftwareTimingDAQ]] = {}

try:
    from .arduino import Arduino_SoftTiming
    DAQ_CONSTRUCTORS.update({BoardType.ARDUINO: Arduino_SoftTiming})
except:
    print('Arduino not available, install pyfirmata')

try:
    from .labjack import LabJackU3_SoftTiming
    DAQ_CONSTRUCTORS.update({BoardType.LABJACK: LabJackU3_SoftTiming})
except:
    print('Labjack not available, install exodriver')

try:
    from .national_instruments import NI_SoftTiming
    DAQ_CONSTRUCTORS.update({BoardType.NATIONAL_INSTRUMENTS: NI_SoftTiming})
except:
    print('National Instruments not available, install nidaqmx')


