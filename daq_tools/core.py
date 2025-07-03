from abc import ABC, abstractmethod
from typing import NamedTuple, List, Union, Dict
import threading
import time
import logging
from enum import IntEnum

logger = logging.getLogger(__name__)

class BoardType(IntEnum):
    ARDUINO = 0
    LABJACK = 1
    NATIONAL_INSTRUMENTS = 2

class BoardInfo(NamedTuple):
    id: Union[int, str]
    name: str
    board_type: BoardType
    analog_output: List[int]
    analog_input: List[int]
    digital_output: List[int]
    digital_input: List[int]
    pwm_output: List[int]
    pwm_input: List[int]

class DAQReadError(Exception):
    """Exception raised for errors in reading from the DAQ device."""
    pass

class SoftwareTimingDAQ(ABC):
    """
    This interface supports basic digital and analog I/O operations, including reading and writing
    digital signals, PWM output, and analog input/output. It is designed primarily for simple use cases 
    involving one channel accessed at a time. Complex multi-channel or 
    concurrent operations are not explicitly supported by this interface.
    Timing and synchronization of I/O operations are handled in software and are not suitable
    for high-precision or real-time applications. Use hardware-timed solutions for such needs.

    Context management is supported to allow usage with 'with' statements, ensuring proper resource cleanup.

    Class methods `list_boards` and `auto_connect` facilitate device discovery and automatic connection.

    Note on non-blocking mode:
    The non-blocking versions of these methods create threads on the fly to run pulses asynchronously.
    Thread creation overhead is typically in the sub-millisecond range (tens to hundreds of microseconds),
    which is generally acceptable for many applications.
    However, because thread scheduling and execution timing depend on the OS and Python runtime,
    these methods should **not** be used for timing-sensitive or real-time applications
    where precise pulse timing and latency guarantees are required.
    """

    @abstractmethod
    def digital_read(self, channel: int) -> float:
        # TODO: ideally you would like to specify PULL_UP / PULL_DOWN vs FLOATING
        # LabJack is pulled up by default
        pass

    @abstractmethod
    def digital_write(self, channel: int, val: bool) -> None:
        pass

    @abstractmethod
    def pwm_write(self, channel: int, duty_cycle: float) -> None:
        pass

    def pwm_read(self, channel: int) -> float:
        # TODO read duty cycle
        pass

    def counter_read(self, channel: int) -> int:
        # TODO count edges
        pass

    def counter_write(self, channel: int, val: int) -> None:
        # TODO send clock at a given frequency
        pass

    @abstractmethod
    def analog_read(self, channel: int) -> float:
        pass

    @abstractmethod
    def analog_write(self, channel: int, val: float) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        """Release any resources held by the DAQ device."""
        pass

    @abstractmethod
    def reset_state(self) -> None:
        """Set all output pins to LOW"""
        pass

    @abstractmethod
    def list_analog_output_channels(self) -> List[int]:
        pass

    @abstractmethod
    def list_analog_input_channels(self) -> List[int]:
        pass

    @abstractmethod
    def list_digital_input_channels(self) -> List[int]:
        pass
    
    @abstractmethod
    def list_digital_output_channels(self) -> List[int]:
        pass

    @abstractmethod
    def list_pwm_output_channels(self) -> List[int]:
        pass

    @abstractmethod
    def list_pwm_input_channels(self) -> List[int]:
        pass

    @classmethod
    @abstractmethod
    def list_boards(cls) -> List[BoardInfo]:
        """Return a list of available DAQ boards connected to the system."""
        pass

    @classmethod
    def auto_connect(cls) -> "SoftwareTimingDAQ":
        boards = cls.list_boards()
        if len(boards) == 1:
            return cls(boards[0].id)
        elif len(boards) == 0:
            raise RuntimeError("No supported board found.")
        else:
            raise RuntimeError(f"Multiple boards found. Please specify one explicitly.")

    def digital_pulse(
            self, 
            channel: int, 
            duration: float, 
            level: bool = True, 
            blocking: bool = True
        ) -> None:

        def do_pulse():
            self.digital_write(channel, level)
            time.sleep(duration)
            self.digital_write(channel, not level)

        if blocking:
            do_pulse()
        else:
            threading.Thread(target=do_pulse, daemon=True).start()

    def pwm_pulse(
            self,
            channel: int,
            duration: float,
            duty_cycle: float,
            blocking: bool = True
        ) -> None:
        
        def do_pwm_pulse():
            self.pwm_write(channel, duty_cycle)
            time.sleep(duration)
            self.pwm_write(channel, 0.0)  

        if blocking:
            do_pwm_pulse()
        else:
            threading.Thread(target=do_pwm_pulse, daemon=True).start()

    def analog_pulse(
            self,
            channel: int,
            duration: float,
            value: float,
            blocking: bool = True
        ) -> None:
        
        def do_analog_pulse():
            self.analog_write(channel, value)
            time.sleep(duration)
            self.analog_write(channel, 0.0)  

        if blocking:
            do_analog_pulse()
        else:
            threading.Thread(target=do_analog_pulse, daemon=True).start()

    def __enter__(self):   
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            logger.warning("Exception occurred during DAQ cleanup in __del__", exc_info=True)


# TODO Work in progress ---

from multiprocessing import Queue, Event, Process
import queue

class HardwareTimingDAQ(ABC):
    
    def get_chunk(self):
        pass
    
    def put_chunk(self):
        pass

class SignalGenerator(Process):
    """ Generates data to send to DAQ for digital / analog write and place on queue """

    def configure(self, stop_event, queue):
        
        self.stop_event = stop_event
        self.queue = queue
    
    def initialize(self):
        pass
        
    def run(self):
        self.initialize()

        while not self.stop_event.is_set():
            data = None
            self.queue.put(data)

        self.cleanup()

    def cleanup(self):
        pass

class DAQ_Reader(Process):
    """ Pulls data from DAQ for digital / analog read and place on queue"""

    def configure(self, stop_event, queue, daq):
        
        self.stop_event = stop_event
        self.queue = queue
        self.daq = daq
    
    @abstractmethod
    def initialize(self):
        pass
        
    def run(self):
        self.initialize()

        while not self.stop_event.is_set():
            data = self.daq.get_chunk()
            self.queue.put(data)

        self.cleanup()

    @abstractmethod
    def cleanup(self):
        pass

class DataHandler(Process):
    """ Do something with data read from DAQ (plot, store, ...) """

    def configure(self, stop_event, queue):
        
        self.stop_event = stop_event
        self.queue = queue

    @abstractmethod    
    def initialize(self):
        pass

    @abstractmethod
    def handle_data(self):
        pass
        
    def run(self):
        self.initialize()

        while not self.stop_event.is_set():
            try:
                data = self.queue.get_nowait()
                self.handle_data(data)
            except queue.Empty:
                pass

        self.cleanup()

    @abstractmethod
    def cleanup(self):
        pass

class DAQ_Writer(Process):
    """ Puts data on the DAQ """

    def configure(self, stop_event, queue, daq):

        self.stop_event = stop_event
        self.queue = queue
        self.daq = daq
    
    def initialize(self):
        pass
        
    def run(self):
        self.initialize()

        while not self.stop_event.is_set():
            try:
                data = self.queue.get_nowait()
                self.daq.put_chunk(data)
            except queue.Empty:
                pass

        self.cleanup()

    def cleanup(self):
        pass

def empty_queue(queue):
    try:
        while True:
            queue.get_nowait()
    except queue.Empty:
        pass

class System(ABC):
    
    def __init__(
            self, 
            daq: HardwareTimingDAQ,
            daq_reader: DAQ_Reader,
            data_handler: DataHandler,
            signal_generator: SignalGenerator,
            daq_writer: DAQ_Writer
        ):

        self.stop_event = Event()
        self.queue_write = Queue(maxsize=2)
        self.queue_read = Queue(maxsize=2)

        self.daq = daq
        self.daq_reader = daq_reader
        self.data_handler = data_handler
        self.signal_generator = signal_generator
        self.daq_writer = daq_writer

        self.daq_reader.configure(self.stop_event, self.queue_read, self.daq)
        self.data_handler.configure(self.stop_event, self.queue_read) 
        self.signal_generator.configure(self.stop_event, self.queue_write)
        self.daq_writer.configure(self.stop_event, self.queue_write, self.daq)  

    def start(self):

        self.data_handler.start()
        self.signal_generator.start()
        self.daq_reader.start()
        self.daq_writer.start()

    def stop(self):
        
        # send stop signal
        self.stop_event.set()

        # empty the queue
        empty_queue(self.queue_read)
        empty_queue(self.queue_write)

        # join
        self.data_handler.join()
        self.signal_generator.join()
        self.daq_reader.join()
        self.daq_writer.join()