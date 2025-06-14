from .core import DigitalAnalogIO
from pyfirmata import Arduino

# NOTE can't use arduino to control PWM freq
class ArduinoDAQ:
    # PWM frequency is around 490Hz on most pins, 
    # and 980Hz on pin 5 and 6

    def __init__(self, board_id: str) -> None:
        self.device = Arduino(board_id)

    def digitalRead(self, channel: int) -> float:
        pin = self.device.get_pin(f'd:{channel}:i')       
        val = pin.read()  
        self.device.taken['digital'][channel] = False
        return val

    def digitalWrite(self, channel: int, val: bool):
        pin = self.device.get_pin(f'd:{channel}:o')
        pin.write(val)
        self.device.taken['digital'][channel] = False

    def pwm(self, channel: int, duty_cycle: float, frequency: float) -> None:
        # frequency is ignored
        pin = self.device.get_pin(f'd:{channel}:p')
        pin.write(duty_cycle)
        self.device.taken['digital'][channel] = False
        
    def analogRead(self, channel: int) -> float:
        pin = self.device.get_pin(f'a:{channel}:i')
        val = pin.read()
        self.device.taken['analog'][channel] = False
        return val

    def analogWrite(self, channel: int, val: float) -> None:
        # Can not do analog write, the arduino does not have a DAC
        print("""The arduino does not have a DAC, no analog writing. 
              Consider hooking a capacitor on a PWM output instead""")

    def close(self) -> None:
        self.device.exit()