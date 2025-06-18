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

    def __init__(self, device_name: str) -> None:

        super().__init__()

        system = nidaqmx.system.System.local()

        self._closed = False
        logger.info(f"Connected to NI : ")
        self.reset_state()

    def analog_write(self, channel: int, val: float) -> None:
        pass

    def analog_read(self, channel: int) -> float:
        pass

    def digital_write(self, channel: int, val: bool) -> None:
        pass

    def digital_read(self, channel: int) -> bool:
        pass

    def pwm_write(self, channel: int, duty_cycle: float) -> None:
        pass

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
        for dev in system.devices:
            print(dev.name)


# analog read  two channels
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai1", min_val=-10.0, max_val=10.0)
    data = task.read(number_of_samples_per_channel=1000)

# analog read multiple points / hardware timings
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
    task.timing.cfg_samp_clk_timing(1000, sample_mode=AcquisitionType.FINITE, samps_per_chan=1000)
    data = task.read(READ_ALL_AVAILABLE)
     
# analog write
with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("NIPCI-6110/ao0")
    task.write([1.1, 2.2, 3.3, 4.4, 5.5], auto_start=True)

# digital read
with nidaqmx.Task() as task:
    task.di_channels.add_di_chan("NIPCI-6110/port0/line0")
    data = task.read()

# digital write
with nidaqmx.Task() as task:
    task.do_channels.add_do_chan("NIPCI-6110/port0/line0")
    task.write(True)

# PWM
with nidaqmx.Task() as task:
    channel = task.co_channels.add_co_pulse_chan_freq("NIPCI-6110/ctr0", duty_cycle=0.5, freq=1000)
    channel.co_pulse_term = "/NIPCI-6110/PFI9"
    task.start()
    task.wait_until_done(timeout=5)
    task.stop()

# stream
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
    stream = AnalogSingleChannelReader(task.in_stream)
    data = np.zeros((1000,), dtype=np.float64)
    stream.read_many_sample(data, number_of_samples_per_channel=1000)
    


import pprint
pp = pprint.PrettyPrinter(indent=4)
system = nidaqmx.system.System.local()
for dev in system.devices:
    pp.pprint(dev.name)
    pp.pprint(dev.ai_physical_chans[:])
    pp.pprint(dev.ao_physical_chans[:])
    pp.pprint(dev.di_lines[:])
    pp.pprint(dev.do_lines[:])
    pp.pprint(dev.ci_physical_chans[:])
    pp.pprint(dev.co_physical_chans[:])
