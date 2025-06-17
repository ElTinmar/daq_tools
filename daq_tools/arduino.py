from .core import DAQ, DAQReadError, BoardInfo
from pyfirmata import Arduino, INPUT, OUTPUT, PWM
from serial.tools import list_ports
from typing import List, Optional
import logging
logger = logging.getLogger(__name__)

SUPPORTED_ARDUINO_BOARDS = {
    ("2341", "0043"), # Official Arduino Uno
    ("1a86", "7523"), # Arduino Nano (clones, CH340)
    ("0403", "6001"), # Arduino Nano (FTDI-based, older boards)
    ("2341", "0058"), # Arduino Nano Every (uses native USB CDC)
    ("2341", "0001"), # Uno Rev2 or variants
}

class Arduino_DAQ(DAQ):

    def __init__(self, board_id: str) -> None:
        
        super().__init__()

        try:
            self.device = Arduino(board_id)
            logger.info(f"Connected to Arduino board: {self.device.name}")
        except Exception as e:
            logger.error(f"Failed to connect to Arduino board: {e}")
            raise
        
        self._closed = False
        self.reset_state()

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
        
        if not getattr(pin, "_reporting_enabled", False):
            pin.enable_reporting()
            pin._reporting_enabled = True  

        val = pin.read()
        if val is None:
            logger.error(f"Read from analog channel {channel} returned None.")
            raise DAQReadError(f"Failed to read from analog channel {channel}.")
        return val

    def analog_write(self, channel: int, val: float) -> None:
        raise NotImplementedError("Arduino does not support analog write, use PWM instead.")

    def close(self) -> None:
        if self._closed:
            return  # Already closed, do nothing
        
        logger.info("Closing Arduino connection, setting outputs off")
        self.reset_state()
        self.device.exit()
        self._closed = True
    
    def reset_state(self):

        logger.info("Resetting all output pins to LOW")

        for pin in self.device.digital:
            try:
                pin.write(False)  
            except Exception as e:
                logger.warning(f"Failed to reset digital pin {pin.pin_number}: {e}")


    @classmethod
    def list_boards(cls) -> List[BoardInfo]:
        ports = list_ports.comports()
        boards = []
        for port in ports:
            vid = f"{port.vid:04x}" if port.vid else None
            pid = f"{port.pid:04x}" if port.pid else None
            if (vid, pid) in SUPPORTED_ARDUINO_BOARDS:
                boards.append(BoardInfo(id=port.device, name=port.description))

        logger.debug(f"Found {len(boards)} supported Arduino board(s).")
        return boards
        
if __name__ == "__main__":

    DIGITAL_PIN = 4
    PWM_PIN = 3

    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    boards = Arduino_DAQ.list_boards()
    print(boards)
    if not boards:
        exit(1)

    with Arduino_DAQ(boards[0].id) as daq:

        # digital
        print('digital write')
        daq.digital_write(DIGITAL_PIN, True)
        time.sleep(2)
        daq.digital_write(DIGITAL_PIN, False)

        # pwm
        print('pwm')
        for j in range(5):
            for i in range(100):
                daq.pwm(PWM_PIN, i/100)
                time.sleep(1/100)
            daq.pwm(PWM_PIN,0)

        # two digital channels
        print('digital write two channels')
        daq.digital_write(DIGITAL_PIN, True)
        daq.digital_write(PWM_PIN, True)
        time.sleep(2)

        # turn off on close

