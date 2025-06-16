from abc import ABC, abstractmethod
from typing import Optional, NamedTuple, List

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
    involving one channel accessed at a time (single-channel usage). Complex multi-channel or 
    concurrent operations are not explicitly supported by this interface.

    Subclasses should implement the hardware-specific logic for each abstract method.

    Context management is supported to allow usage with 'with' statements, ensuring proper resource cleanup.

    Class methods `list_boards` and `auto_connect` facilitate device discovery and automatic connection.
    """

    @abstractmethod
    def digital_read(self, channel: int) -> float:
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