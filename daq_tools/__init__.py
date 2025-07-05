from .core import SoftwareTimingDAQ, BoardInfo, DAQReadError, BoardType
from .arduino import Arduino_SoftTiming
from .labjack import LabJackU3_SoftTiming
from .national_instruments import NI_SoftTiming
from typing import Dict, Type

DAQ_CONSTRUCTORS: Dict[BoardType, Type[SoftwareTimingDAQ]] = {
    BoardType.ARDUINO: Arduino_SoftTiming,
    BoardType.LABJACK: LabJackU3_SoftTiming,
    BoardType.NATIONAL_INSTRUMENTS: NI_SoftTiming
}