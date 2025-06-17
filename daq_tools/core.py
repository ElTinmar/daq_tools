from abc import ABC, abstractmethod
from typing import Optional, NamedTuple, List
import threading
import time

# TODO: set default pin state on startup
# TODO: set default pin state on close

class BoardInfo(NamedTuple):
    id: int
    name: str

# maybe add counter, timer
class DAQReadError(Exception):
    """Exception raised for errors in reading from the DAQ device."""
    pass

class DAQ(ABC):
    """
    Abstract base class defining a common interface for Data Acquisition (DAQ) devices.

    This interface supports basic digital and analog I/O operations, including reading and writing
    digital signals, PWM output, and analog input/output. It is designed primarily for simple use cases 
    involving one channel accessed at a time. Complex multi-channel or 
    concurrent operations are not explicitly supported by this interface.
    Timing and synchronization of I/O operations are handled in software and are not suitable
    for high-precision or real-time applications. Use hardware-timed solutions for such needs.

    Context management is supported to allow usage with 'with' statements, ensuring proper resource cleanup.

    Class methods `list_boards` and `auto_connect` facilitate device discovery and automatic connection.
    """

    @abstractmethod
    def supports_digital_read(self) -> bool:
        pass 

    @abstractmethod
    def supports_digital_write(self) -> bool:
        pass 

    @abstractmethod
    def supports_analog_read(self) -> bool:
        pass 

    @abstractmethod
    def supports_analog_write(self) -> bool:
        pass 

    @abstractmethod
    def supports_pwm(self) -> bool:
        pass 

    @abstractmethod
    def digital_read(self, channel: int) -> float:
        # TODO: ideally you would like to specify PULL_UP / PULL_DOWN vs FLOATING
        # LabJack is pulled up by default
        pass

    @abstractmethod
    def digital_write(self, channel: int, val: bool) -> None:
        pass

    @abstractmethod
    def pwm(self, channel: int, duty_cycle: float, frequency: Optional[float]) -> None:
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

    def __enter__(self):   
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @classmethod
    @abstractmethod
    def list_boards(cls) -> List[BoardInfo]:
        """Return a list of available DAQ boards connected to the system."""
        pass

    @classmethod
    @abstractmethod
    def auto_connect(cls) -> "DAQ":
        """Automatically detect and connect to a DAQ device, returning an instance."""
        pass

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
            frequency: float,
            blocking: bool = True
        ) -> None:
        
        def do_pwm_pulse():
            self.pwm(channel, duty_cycle, frequency)
            time.sleep(duration)
            self.pwm(channel, 0.0, frequency)  

        if blocking:
            do_pwm_pulse()
        else:
            threading.Thread(target=do_pwm_pulse, daemon=True).start()
