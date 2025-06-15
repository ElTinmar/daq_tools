from .core import DAQ
from pyfirmata import Arduino
from serial.tools import list_ports
import logging
logging.basicConfig(level=logging.INFO)

SUPPORTED_ARDUINO_BOARDS = {
    ("2341", "0043"), # Official Arduino Uno
    ("1a86", "7523"), # Arduino Nano (clones, CH340)
    ("0403", "6001"), # Arduino Nano (FTDI-based, older boards)
    ("2341", "0058"), # Arduino Nano Every (uses native USB CDC)
    ("2341", "0001"), # Uno Rev2 or variants
}

# NOTE can't use arduino to control PWM freq
class Arduino_DAQ(DAQ):
    # PWM frequency is around 490Hz on most pins,
    # and 980Hz on pin 5 and 6

    def __init__(self, board_id: str) -> None:
        self.device = Arduino(board_id)
        logging.info(f"Connected to Arduino board: {self.device.name}")

    def digital_read(self, channel: int) -> float:
        pin = self.device.get_pin(f'd:{channel}:i')       
        val = pin.read()  
        self.device.taken['digital'][channel] = False
        return val

    def digital_write(self, channel: int, val: bool):
        pin = self.device.get_pin(f'd:{channel}:o')
        pin.write(val)
        self.device.taken['digital'][channel] = False

    def pwm(self, channel: int, duty_cycle: float, frequency: float) -> None:
        # frequency is ignored
        pin = self.device.get_pin(f'd:{channel}:p')
        pin.write(duty_cycle)
        self.device.taken['digital'][channel] = False
        
    def analog_read(self, channel: int) -> float:
        pin = self.device.get_pin(f'a:{channel}:i')
        val = pin.read()
        self.device.taken['analog'][channel] = False
        return val

    def analog_write(self, channel: int, val: float) -> None:
        # Can not do analog write, the arduino does not have a DAC
        print("""The arduino does not have a DAC, no analog writing. 
              Consider hooking a capacitor on a PWM output instead""")

    def close(self) -> None:
        self.device.exit()

    @classmethod
    def list_boards(cls):
        ports = list_ports.comports()

        for port in ports:
            vid = f"{port.vid:04x}" if port.vid else None
            pid = f"{port.pid:04x}" if port.pid else None
            if (vid, pid) in SUPPORTED_ARDUINO_BOARDS:
                print(port.device, port.description)

if __name__ == "__main__":

    # Example usage
    daq = Arduino_DAQ('/dev/ttyUSB0')  
    daq.digital_write(13, True) 
    print(daq.digital_read(13))  
    daq.close()
