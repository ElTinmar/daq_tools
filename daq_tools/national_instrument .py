import nidaqmx
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE
from nidaqmx.stream_readers import AnalogSingleChannelReader, DigitalSingleChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter, DigitalSingleChannelWriter
import numpy as np
from typing import List
from .core import SoftwareTimingDAQ, BoardInfo
import logging
logger = logging.getLogger(__name__)

# https://github.com/ni/nidaqmx-python/tree/master/examples 

class NI_SoftTiming(SoftwareTimingDAQ):

    def __init__(self, device_index: int) -> None:

        super().__init__()

        system = nidaqmx.system.System.local()
        self.device = system.devices[device_index] 
        self._closed = False
        logger.info(f"Connected to NI: {self.device.name}")
        self.reset_state()

    def analog_write(self, channel: int, val: float) -> None:
        ao_channel = self.device.ao_physical_chans[channel]
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(ao_channel.name) 
            task.write(val)

    def analog_read(self, channel: int) -> float:
        ai_channel = self.device.ai_physical_chans[channel]
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(ai_channel.name) 
            val = task.read()
        return val

    def digital_write(self, channel: int, val: bool) -> None:
        do_channel = self.device.do_lines[channel]
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(do_channel.name)
            task.write(val)

    def digital_read(self, channel: int) -> bool:
        di_channel = self.device.di_lines[channel]
        with nidaqmx.Task() as task:
            task.di_channels.add_di_chan(di_channel.name)
            val = task.read()
        return val

    def pwm_write(self, channel: int, duty_cycle: float) -> None:
        pwm_channel = self.device.co_physical_chans[channel]
        with nidaqmx.Task() as task: 
            task.co_channels.add_co_pulse_chan_freq(
                pwm_channel.name, 
                duty_cycle = duty_cycle, 
                freq = 1000,
            )

    def close(self) -> None:
        if self._closed:
            return 

        logger.info("Closing NI card, setting outputs off")
        self.reset_state()
        self.device.close()
        self._closed = True
    
    def reset_state(self):
        # reset config 
        # set outputs to zero
        pass

    @classmethod
    def list_boards(cls) -> List[BoardInfo]:
        system = nidaqmx.system.System.local()
        boards = []
        for idx, dev in enumerate(system.devices):
            boards.append(BoardInfo(id=idx, name=dev.name))

        logger.debug(f"Found {len(boards)} supported U3 board(s).")
        return boards

# stream
#with nidaqmx.Task() as task:
#    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
#    stream = AnalogSingleChannelReader(task.in_stream)
#    data = np.zeros((1000,), dtype=np.float64)
#    stream.read_many_sample(data, number_of_samples_per_channel=1000)
    
