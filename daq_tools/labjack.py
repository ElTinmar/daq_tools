from .core import DAQ, BoardInfo
import u3
from LabJackPython import listAll
from typing import NamedTuple, List

import logging
logger = logging.getLogger(__name__)

# https://github.com/labjack/LabJackPython
# https://support.labjack.com/docs/ud-modbus-old-deprecated

class LabJack_U3_DAQ(DAQ):
    '''
    Use LabJack to read and write from a single pin at a time.
    Supports Analog input (FIOs) and output (DACs), digital
    input and output (FIOs), as well as PWM (FIOs). 

    The U3 has 2 timers (Timer0-Timer1) and 2 counters (Counter0-Counter1). 
    When any of these timers or counters are enabled, they take over an
    FIO/EIO line in sequence (Timer0, Timer1, Counter0, then Counter1), 
    starting with FIO0+TimerCounterPinOffset. 
    '''
  
    # Analog outputs (they can also do input, but I decided to ignore that)
    # 10 bit resolution
    # [0.04V, 4.95V]
    DAC0 = 5000
    DAC1 = 5002

    # Digital Input/Output
    DIO0 = 6000
    DIO1 = 6001
    DIO2 = 6002
    DIO3 = 6003
    DIO4 = 6004
    DIO5 = 6005
    DIO6 = 6006
    DIO7 = 6007

    # 12 bits resolution
    # single-ended: [0V, 2.44V]
    # differential: [-2.44V, 2.44V] 
    # special: [0V, 3.6V] 
    AIN0 = 0
    AIN1 = 2
    AIN2 = 4
    AIN3 = 6
    AIN4 = 8
    AIN5 = 10
    AIN6 = 12
    AIN7 = 14

    # configure FIO as analog or digital
    # bitmask: 1=Analog, 0=digital
    FIO_ANALOG = 50590

    channels = {
        'AnalogInput': [AIN0,AIN1,AIN2,AIN3,AIN4,AIN5,AIN6,AIN7],
        'AnalogOutput': [DAC0,DAC1],
        'DigitalInputOutput': [DIO0,DIO1,DIO2,DIO3,DIO4,DIO5,DIO6,DIO7]
    }

    TIMER_CLOCK_BASE = 7000
    TIMER_CLOCK_DIVISOR = 7002
    NUM_TIMER_ENABLED = 50501
    TIMER_PIN_OFFSET = 50500
    TIMER_CONFIG = 7100
    TIMER_MODE_16BIT = 0
    TIMER_MODE_8BIT = 1

    class Clock(NamedTuple):
        register: int
        frequency_Hz: int

    CLOCK_BASE = {
        '4MHz': Clock(0, 4_000_000),
        '12MHz': Clock(1, 12_000_000),
        '48MHz(Default)': Clock(2, 48_000_000),
        '1MHz/Divisor': Clock(3, 1_000_000),
        '4MHz/Divisor': Clock(4, 4_000_000),
        '12MHz/Divisor': Clock(5, 12_000_000),
        '48MHz/Divisor': Clock(6, 48_000_000)
    }

    def __init__(self, serial_number: int) -> None:

        super().__init__()
        
        self.device = u3.U3(serial = serial_number)
        logger.info(f"Connected to LabJack U3 S/N: {self.device.serialNumber}")
        self._closed = False
        self.reset_state()

    def analog_write(self, channel: int, val: float) -> None:
        # DAC uses PWM internally. Reset clock to default settings to avoid interactions
        # with PWM
        self.device.writeRegister(self.TIMER_CLOCK_BASE, self.CLOCK_BASE['48MHz(Default)'].register)
        self.device.writeRegister(self.TIMER_CLOCK_DIVISOR, 0) # just to be extra careful
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        self.device.writeRegister(self.channels['AnalogOutput'][channel], val)

    def analog_read(self, channel: int) -> float:
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        # Set the FIO pin to analog mode using a bitmask
        bitmask = 1 << channel
        self.device.writeRegister(self.FIO_ANALOG, bitmask) # set channel as analog
        return self.device.readRegister(self.channels['AnalogInput'][channel])
    
    def digital_write(self, channel: int, val: bool):
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        self.device.writeRegister(self.FIO_ANALOG, 0) # set all channels as digital
        self.device.writeRegister(self.channels['DigitalInputOutput'][channel], val)

    def digital_read(self, channel: int) -> float:
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        self.device.writeRegister(self.FIO_ANALOG, 0) # set channel as digital
        return self.device.readRegister(self.channels['DigitalInputOutput'][channel])
   
    def pwm(self, channel: int = 4, duty_cycle: float = 0.5, frequency: float = 732.42) -> None:

        if not (0 <= duty_cycle <= 1):
            raise ValueError('duty_cycle should be between 0 and 1')

        if frequency > 187_500:
            raise ValueError('max frequency at 48MHz is 187_500 Hz')
        elif frequency < 2.861:
            raise ValueError('min frequency at 48MHz is 2.861 Hz')
         
        if frequency > 732.42:
            timer_mode = self.TIMER_MODE_8BIT
            div = 2**8
        else:
            timer_mode = self.TIMER_MODE_16BIT
            div = 2**16

        # make sure digital value is 0
        self.digital_write(channel, 0)

        if duty_cycle == 0:
            # PWM can't fully turn off. Use digital write instead
            # and return
            return
        
        # enable Timer0 
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 1)

        # set the timer clock to 48 MHz with divisor
        self.device.writeRegister(self.TIMER_CLOCK_BASE, self.CLOCK_BASE['48MHz/Divisor'].register)

        # divisor should be in the range 0-255, 0 corresponds to a divisor of 256
        timer_clock_divisor = int(self.CLOCK_BASE['48MHz/Divisor'].frequency_Hz/(frequency * div))
        if timer_clock_divisor == 256: timer_clock_divisor = 0 

        # set divisor
        self.device.writeRegister(self.TIMER_CLOCK_DIVISOR, timer_clock_divisor)

        # Pin offset (FIO) 
        self.device.writeRegister(self.TIMER_PIN_OFFSET, channel) 

        # 16 bit value for duty cycle (8bit timer mode: LSB is ignored)
        value = int(65535*(1-duty_cycle))

        # Configure the timer for 16-bit PWM
        self.device.writeRegister(self.TIMER_CONFIG, [timer_mode, value]) 

    def close(self) -> None:
        if self._closed:
            return  

        logger.info("Closing LabJack connection, setting outputs off")
        self.reset_state()
        self.device.close()
        self._closed = True

    def reset_state(self):

        logger.info("Resetting all output pins to LOW")
        
        for channel in range(len(self.channels['DigitalInputOutput'])):
            try:
                self.digital_write(channel, False)
            except Exception as e:
                logger.warning(f"Failed to reset digital channel {channel}: {e}")

        for channel in range(len(self.channels['AnalogOutput'])):
            try:
                self.analog_write(channel, 0)
            except Exception as e:
                logger.warning(f"Failed to reset analog channel {channel}: {e}")

    @classmethod
    def list_boards(cls) -> List[BoardInfo]:
        u3s = listAll(3) # get all U3 boards
        boards = []
        for id, info in u3s.items():
            boards.append(BoardInfo(id=info['serialNumber'], name=info['deviceName']))

        logger.debug(f"Found {len(boards)} supported U3 board(s).")
        return boards

if __name__ == "__main__":

    DIGITAL_PIN = 0
    PWM_PIN = 4

    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    boards = LabJack_U3_DAQ.list_boards()
    print(boards)
    if not boards:
        exit(1)

    with LabJack_U3_DAQ(boards[0].id) as daq:
        
        # digital
        print('digital write')
        daq.digital_write(DIGITAL_PIN, True)
        time.sleep(2)
        daq.digital_write(DIGITAL_PIN, False)

        # pwm
        print('pwm')
        for j in range(5):
            for i in range(100):
                daq.pwm(PWM_PIN, i/100, 1000)
                time.sleep(1/100)
            daq.pwm(PWM_PIN,0,1000)

        # analog
        print('analog write')
        daq.analog_write(0, 1.75)
        time.sleep(2)
        daq.analog_write(0, 0)

        # two digital channels
        print('digital write two channels')
        daq.digital_write(DIGITAL_PIN, True)
        daq.digital_write(PWM_PIN, True)
        time.sleep(2)

        # turn off on close




