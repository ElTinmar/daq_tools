import nidaqmx
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE
from nidaqmx.stream_readers import AnalogSingleChannelReader, DigitalSingleChannelReader
from nidaqmx.stream_writers import AnalogSingleChannelWriter, DigitalSingleChannelWriter
import numpy as np
from typing import List
from .core import SoftwareTimingDAQ, BoardInfo, HardwareTimingDAQ
import logging
logger = logging.getLogger(__name__)

# https://github.com/ni/nidaqmx-python/tree/master/examples 

class NI_SoftTiming(SoftwareTimingDAQ):

    def __init__(
            self, 
            device_index: int, 
            pwm_frequency: float = 1000
        ) -> None:

        super().__init__()

        self.pwm_frequency = pwm_frequency

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
        # TODO check wether duty_cycle in bounds
        duty_cycle = max(0.001, min(duty_cycle, 0.999))
        pwm_channel = self.device.co_physical_chans[channel]
        with nidaqmx.Task() as task: 
            task.co_channels.add_co_pulse_chan_freq(
                pwm_channel.name, 
                duty_cycle = duty_cycle, 
                freq = self.pwm_frequency,
            )
            task.start()

    def close(self) -> None:
        if self._closed:
            return 

        logger.info("Closing NI card, setting outputs off")
        self.reset_state()
        # TODO close device?
        self._closed = True
    
    def reset_state(self):
        # TODO
        # reset config 
        # set outputs to zero
        pass

    @classmethod
    def list_boards(cls) -> List[BoardInfo]:
        system = nidaqmx.system.System.local()
        boards = []
        for idx, dev in enumerate(system.devices):
            boards.append(BoardInfo(id=idx, name=dev.name))

        logger.debug(f"Found {len(boards)} supported NI board(s).")
        return boards

# TODO Work in progress ---

# stream
#with nidaqmx.Task() as task:
#    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
#    stream = AnalogSingleChannelReader(task.in_stream)
#    data = np.zeros((1000,), dtype=np.float64)
#    stream.read_many_sample(data, number_of_samples_per_channel=1000)
    
class NI_HardTiming(HardwareTimingDAQ):
    
    def get_chunk(self):
        pass

    def put_chunk(self):
        pass

# ----- Work in progress

if __name__ == "__main__":

    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    boards = NI_SoftTiming.list_boards()
    print(boards)
    if not boards:
        exit(1)

    with NI_SoftTiming(boards[0].id) as daq:
        
        # digital
        logging.info('Digital ON FIO2')
        daq.digital_write(0, True)
        time.sleep(2)
        daq.digital_write(0, False)

        # pwm_write
        logging.info('PWM FIO4')
        for j in range(5):
            for i in range(100):
                daq.pwm_write(0, i/100)
                time.sleep(1/100)
            daq.pwm_write(0,0)

        # analog
        logging.info('Analog write DAC0')
        for j in range(5):
            for i in range(100):
                daq.analog_write(0, 1.75*i/100)
                time.sleep(1/100)
        daq.analog_write(0, 0)
        time.sleep(1)

        # turn on everything 
        logging.info('Turn everything on')
        daq.analog_write(0, 1.75)
        time.sleep(1)
        daq.digital_write(2, True)
        time.sleep(1)
        daq.digital_write(0, True)
        time.sleep(1)
        daq.pwm_write(0, 0.025)
        time.sleep(1)
        daq.pwm_write(1, 0.25)
        time.sleep(1)
