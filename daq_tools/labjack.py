from .core import DAQ
import u3

class LabJack_U3LV_DAQ(DAQ):
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

    CLOCK: int = 48 # I'm only using the 48MHz clock with divisors enabled 
        
    def __init__(self) -> None:
        
        self.device = u3.U3()

    def analog_write(self, channel: int, val: float) -> None:
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        self.device.writeRegister(self.channels['AnalogOutput'][channel], val)

    def analog_read(self, channel: int) -> float:
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        self.device.writeRegister(self.FIO_ANALOG, channel**2) # set channel as analog
        return self.device.readRegister(self.channels['AnalogInput'][channel])
    
    def digital_write(self, channel: int, val: bool):
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 0)
        self.device.writeRegister(self.FIO_ANALOG, 0) # set channel as digital
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
        self.digitalWrite(channel,0)

        if duty_cycle == 0:
            # PWM can't fully turn off. Use digital write instead
            # and return
            return
        
        # divisor should be in the range 0-255, 0 corresponds to a divisor of 256
        timer_clock_divisor = int( (self.CLOCK * 1e6)/(frequency * div) )
        if timer_clock_divisor == 256: timer_clock_divisor = 0 
        
        # enable Timer0 
        self.device.writeRegister(self.NUM_TIMER_ENABLED, 1)

        # set the timer clock to 48 MHz with divisor (correspond to register value of 6)
        self.device.writeRegister(self.TIMER_CLOCK_BASE, 6)

        # set divisor
        self.device.writeRegister(self.TIMER_CLOCK_DIVISOR, timer_clock_divisor)

        # Pin offset (FIO) 
        self.device.writeRegister(self.TIMER_PIN_OFFSET, channel) 

        # 16 bit value for duty cycle
        value = int(65535*(1-duty_cycle))

        # Configure the timer for 16-bit PWM
        self.device.writeRegister(self.TIMER_CONFIG, [timer_mode, value]) 

    def close(self) -> None:
        self.device.close()

