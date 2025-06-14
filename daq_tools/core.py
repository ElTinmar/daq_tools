from abc import ABC, abstractmethod

class DigitalAnalogIO(ABC):

    @abstractmethod
    def digitalRead(self, channel: int) -> float:
        pass

    @abstractmethod
    def digitalWrite(self, channel: int, val: bool) -> None:
        pass

    @abstractmethod
    def pwm(self, channel: int, duty_cycle: float, frequency: float) -> None:
        pass
        
    @abstractmethod
    def analogRead(self, channel: int) -> float:
        pass

    @abstractmethod
    def analogWrite(self, channel: int, val: float) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass