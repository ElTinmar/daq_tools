from .core import DAQ, DAQReadError
from pyfirmata import Arduino, INPUT, OUTPUT, PWM
from serial.tools import list_ports
from typing import List, Optional, NamedTuple
import logging

logger = logging.getLogger(__name__)

SUPPORTED_ARDUINO_BOARDS = {
    ("2341", "0043"), # Official Arduino Uno
    ("1a86", "7523"), # Arduino Nano (clones, CH340)
    ("0403", "6001"), # Arduino Nano (FTDI-based, older boards)
    ("2341", "0058"), # Arduino Nano Every (uses native USB CDC)
    ("2341", "0001"), # Uno Rev2 or variants
}

class ArduinoBoardInfo(NamedTuple):
    device: str
    description: str

class Arduino_DAQ(DAQ):

    def __init__(self, board_id: str) -> None:
        
        super().__init__()

        try:
            self.device = Arduino(board_id)
            logger.info(f"Connected to Arduino board: {self.device.name}")
        except Exception as e:
            logger.error(f"Failed to connect to Arduino board: {e}")
            raise

    def digital_read(self, channel: int) -> float:
        try:
            pin = self.device.digital[channel]
        except IndexError:
            raise ValueError(f"Invalid channel {channel}. Valid channels are 0 to {len(self.device.digital) - 1}.")
        pin.mode = INPUT         
        val = pin.read()
        if val is None:
            logger.error(f"Read from digital channel {channel} returned None.")  
            raise DAQReadError(f"Failed to read from digital channel {channel}.")
        return val

    def digital_write(self, channel: int, val: bool) -> None:
        try:
            pin = self.device.digital[channel]
        except IndexError:
            raise ValueError(f"Invalid channel {channel}. Valid channels are 0 to {len(self.device.digital) - 1}.")
        pin.mode = OUTPUT
        pin.write(val)

    def pwm(self, channel: int, duty_cycle: float, frequency: Optional[float] = None) -> None:
        """
        Set PWM on a pin with a duty cycle (0.0 to 1.0).
        Note: Arduino's PWM frequency cannot be changed via pyfirmata.
        By default, PWM frequency is around 490Hz on most pins, and 980Hz on pin 5 and 6.
        The frequency parameter is ignored.
        """

        try:
            pin = self.device.digital[channel]
        except IndexError:
            raise ValueError(f"Invalid channel {channel}. Valid channels are 0 to {len(self.device.digital) - 1}.")
        pin.mode = PWM
        pin.write(duty_cycle)
        
    def analog_read(self, channel: int) -> float:
        try:
            pin = self.device.analog[channel]
        except IndexError:
            raise ValueError(f"Invalid channel {channel}. Valid channels are 0 to {len(self.device.analog) - 1}.")
        pin.enable_reporting()
        val = pin.read()
        if val is None:
            logger.error(f"Read from analog channel {channel} returned None.")
            raise DAQReadError(f"Failed to read from analog channel {channel}.")
        return val

    def analog_write(self, channel: int, val: float) -> None:
        raise NotImplementedError("Arduino does not support analog write, use PWM instead.")

    def close(self) -> None:
        logger.info("Closing Arduino connection.")
        self.device.exit()

    @classmethod
    def list_boards(cls) -> List[ArduinoBoardInfo]:
        ports = list_ports.comports()
        boards = []
        for port in ports:
            vid = f"{port.vid:04x}" if port.vid else None
            pid = f"{port.pid:04x}" if port.pid else None
            if (vid, pid) in SUPPORTED_ARDUINO_BOARDS:
                boards.append(ArduinoBoardInfo(port.device, port.description))

        logger.debug(f"Found {len(boards)} supported Arduino board(s).")
        return boards

    @classmethod
    def auto_connect(cls) -> "Arduino_DAQ":
        boards = cls.list_boards()
        if len(boards) == 1:
            return cls(boards[0].device)
        elif len(boards) == 0:
            raise RuntimeError("No supported Arduino boards found.")
        else:
            raise RuntimeError(f"Multiple boards found. Please specify one explicitly.")
        
if __name__ == "__main__":

    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    boards = Arduino_DAQ.list_boards()
    print(boards)
    if not boards:
        exit(1)

    daq = Arduino_DAQ(boards[0].device)
    daq.digital_write(11, True)
    time.sleep(1)
    daq.digital_write(11, False)
    daq.close()
