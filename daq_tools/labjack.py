from .core import SoftwareTimingDAQ, BoardInfo, BoardType
import u3
from LabJackPython import listAll
from typing import NamedTuple, List

import logging
logger = logging.getLogger(__name__)

# https://github.com/labjack/LabJackPython
# https://support.labjack.com/docs/ud-modbus-old-deprecated

class LabJackU3_SoftTiming(SoftwareTimingDAQ):
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

    CLOCK_BASE = {
        '4MHz': 0,
        '12MHz': 1,
        '48MHz(Default)': 2,
        '1MHz/Divisor': 3,
        '4MHz/Divisor': 4,
        '12MHz/Divisor': 5,
        '48MHz/Divisor': 6
    }

    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        
        self.device = u3.U3(serial = self.board_id)
        logger.info(f"Connected to LabJack U3 S/N: {self.device.serialNumber}")
        self.pwm_pins = {4, 5}
        self._closed = False
        self.reset_state()

    def analog_write(self, channel: int, val: float) -> None:
        self.device.writeRegister(self.channels['AnalogOutput'][channel], val)

    def analog_read(self, channel: int) -> float:
        # Set the FIO pin to analog mode using a bitmask
        bitmask = 1 << channel
        self.device.writeRegister(self.FIO_ANALOG, bitmask) # set channel as analog
        return self.device.readRegister(self.channels['AnalogInput'][channel])
    
    def digital_write(self, channel: int, val: bool):
        if channel in self.pwm_pins:
            raise ValueError(f'digital write not available on PWM pins {self.pwm_pins}')

        self.device.writeRegister(self.FIO_ANALOG, 0) # set all channels as digital
        self.device.writeRegister(self.channels['DigitalInputOutput'][channel], val)

    def digital_read(self, channel: int) -> float:
        if channel in self.pwm_pins:
            raise ValueError(f'digital read not available on PWM pins {self.pwm_pins}')

        self.device.writeRegister(self.FIO_ANALOG, 0) # set channel as digital
        return self.device.readRegister(self.channels['DigitalInputOutput'][channel])
   
    def pwm_write(self, channel: int = 4, duty_cycle: float = 0.5) -> None:
        # PWM on FIO4 and FIO5, PWM frequency fixed in init

        if channel not in self.pwm_pins:
            raise ValueError(f'PWM only available on pins {self.pwm_pins}')

        channel_offset = channel-4

        if not (0 <= duty_cycle <= 1):
            raise ValueError('duty_cycle should be between 0 and 1')

        # 16 bit value for duty cycle (8bit timer mode: LSB is ignored)
        value = int(65535*(1-duty_cycle))

        # Configure the timer for 16-bit PWM
        self.device.writeRegister(self.TIMER_CONFIG + (channel_offset*2), [self.TIMER_MODE_16BIT, value]) 

    def pwm_read(self, channel: int) -> float:
        # TODO read duty cycle 
        pass

    def counter_read(self, channel: int) -> int:
        # TODO count edges
        pass

    def counter_write(self, channel: int, val: int) -> None:
        # TODO send clock at a given frequency
        pass

    def close(self) -> None:
        if self._closed:
            return  

        logger.info("Closing LabJack connection, setting outputs off")
        self.reset_state()
        self.device.close()
        self._closed = True

    def reset_state(self):
        
        logger.info("Configure device: 2 timers @ 48MHz, no prescaler on pins FIO4 and FIO5 ")

        self.device.writeRegister(self.NUM_TIMER_ENABLED, 2) 
        self.device.writeRegister(self.TIMER_PIN_OFFSET, 4) 
        self.device.writeRegister(self.TIMER_CLOCK_BASE, self.CLOCK_BASE['48MHz(Default)']) 
        self.device.writeRegister(self.TIMER_CLOCK_DIVISOR, 0) 

        logger.info("Resetting all output pins to LOW")
        
        for channel in range(len(self.channels['DigitalInputOutput'])):
            try:
                if channel in self.pwm_pins:
                    self.pwm_write(channel, 0)
                else:
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
            with cls(info['serialNumber']) as labjack:
                boards.append(BoardInfo(
                    id = info['serialNumber'], 
                    name = info['deviceName'],
                    board_type = BoardType.LABJACK,
                    analog_input = labjack.list_analog_input_channels(),
                    analog_output = labjack.list_analog_output_channels(),
                    digital_input = labjack.list_digital_input_channels(),
                    digital_output = labjack.list_digital_output_channels(),
                    pwm_input = labjack.list_pwm_input_channels(),
                    pwm_output = labjack.list_pwm_output_channels()
                ))

        logger.debug(f"Found {len(boards)} supported U3 board(s).")
        return boards

    def list_analog_output_channels(self) -> List[int]:
        return [idx for idx, reg in enumerate(self.channels['AnalogOutput'])]

    def list_analog_input_channels(self) -> List[int]:
        return [idx for idx, reg in enumerate(self.channels['AnalogInput'])]

    def list_digital_input_channels(self) -> List[int]:
        return [idx for idx, reg in enumerate(self.channels['DigitalInputOutput']) if idx not in self.pwm_pins]
    
    def list_digital_output_channels(self) -> List[int]:
        return self.list_digital_input_channels()

    def list_pwm_output_channels(self) -> List[int]:
        return list(self.pwm_pins)

    def list_pwm_input_channels(self) -> List[int]:
        # TODO: not implemented yet
        return []

# TODO Labjack in streaming mode
# Labjack can only stream analog inputs

if __name__ == "__main__":

    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    boards = LabJackU3_SoftTiming.list_boards()
    print(boards)
    if not boards:
        exit(1)

    with LabJackU3_SoftTiming(boards[0].id) as daq:
        
        # digital
        logging.info('Digital ON FIO2')
        daq.digital_write(0, True)
        time.sleep(2)
        daq.digital_write(0, False)

        # pwm_write
        logging.info('PWM FIO4')
        for j in range(5):
            for i in range(100):
                daq.pwm_write(4, i/100)
                time.sleep(1/100)
            daq.pwm_write(4,0)

        # analog
        logging.info('Analog write DAC0')
        for j in range(5):
            for i in range(100):
                daq.analog_write(0, 1.75*i/100)
                time.sleep(1/100)
        daq.analog_write(0, 0)
        time.sleep(1)

        # turn on everything 
        logging.info('Turn everything on')
        daq.analog_write(0, 1.75)
        time.sleep(1)
        daq.digital_write(2, True)
        time.sleep(1)
        daq.digital_write(0, True)
        time.sleep(1)
        daq.pwm_write(4, 0.025)
        time.sleep(1)
        daq.pwm_write(5, 0.25)
        time.sleep(1)



