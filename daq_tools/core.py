from abc import ABC, abstractmethod, abstractclassmethod
from typing import Optional, NamedTuple, List

class BoardInfo(NamedTuple):
    id: int
    name: str

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

    def __enter__(self):   
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractclassmethod
    def list_boards(cls) -> List[BoardInfo]:
        pass

    @abstractclassmethod
    def auto_connect(cls) -> "DAQ":
        pass