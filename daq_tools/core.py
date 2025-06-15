from abc import ABC, abstractmethod
from typing import Optional

# maybe add counter, timer

class DAQReadError(Exception):
    """Exception raised for errors in reading from the DAQ device."""
    pass

class DAQ(ABC):

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
        pass