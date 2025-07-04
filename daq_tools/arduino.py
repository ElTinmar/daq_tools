from .core import SoftwareTimingDAQ, DAQReadError, BoardInfo, BoardType
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

class Arduino_SoftTiming(SoftwareTimingDAQ):

    def __init__(self, *args, **kwargs) -> None:
        
        super().__init__(*args, **kwargs)

        try:
            self.device = Arduino(self.board_id)
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
        
        if pin.PWM_CAPABLE:
            raise ValueError(f'digital read not available on PWM pin')
        
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
        
        if pin.PWM_CAPABLE:
            raise ValueError(f'digital write not available on PWM pin')
        
        pin.mode = OUTPUT
        pin.write(val)

    def pwm_write(self, channel: int, duty_cycle: float) -> None:
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
                with cls(port.device) as arduino:
                    boards.append(BoardInfo(
                        id = port.device, 
                        name = port.description,
                        board_type = BoardType.ARDUINO,
                        analog_input = arduino.list_analog_input_channels(),
                        analog_output = arduino.list_analog_output_channels(),
                        digital_input = arduino.list_digital_input_channels(),
                        digital_output = arduino.list_digital_output_channels(),
                        pwm_input = arduino.list_pwm_input_channels(),
                        pwm_output = arduino.list_pwm_output_channels()
                    ))

        logger.debug(f"Found {len(boards)} supported Arduino board(s).")
        return boards
    
    def list_analog_output_channels(self) -> List[int]:
        return []

    def list_analog_input_channels(self) -> List[int]:
        return [idx for idx, pin in enumerate(self.device.analog)]
    
    def list_digital_input_channels(self) -> List[int]:
        return [idx for idx, pin in enumerate(self.device.digital) if not pin.PWM_CAPABLE]
    
    def list_digital_output_channels(self) -> List[int]:
        return self.list_digital_input_channels()

    def list_pwm_output_channels(self) -> List[int]:
        return [idx for idx, pin in enumerate(self.device.digital) if pin.PWM_CAPABLE]

    def list_pwm_input_channels(self) -> List[int]:
        return []
        
if __name__ == "__main__":

    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    boards = Arduino_SoftTiming.list_boards()
    print(boards)
    if not boards:
        exit(1)

    with Arduino_SoftTiming(boards[0].id) as daq:

        # pwm_write
        logging.info('PWM FIO4')
        for j in range(5):
            for i in range(100):
                daq.pwm_write(3, i/100)
                time.sleep(1/100)
            daq.pwm_write(3,0)

        # digital
        logging.info('Digital ON ')
        daq.digital_write(4, True)
        time.sleep(2)
        daq.digital_write(4, False)
        time.sleep(1)

        # turn on everything
        logging.info('Turn everything on')
        daq.pwm_write(3, 0.025)
        time.sleep(1)
        daq.digital_write(4, True)
        time.sleep(1)
        daq.digital_write(8, True)
        time.sleep(1)
        daq.pwm_write(9, 0.25)
        time.sleep(1)
        
