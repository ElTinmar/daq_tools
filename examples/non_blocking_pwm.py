from daq_tools import Arduino_SoftTiming
import logging

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    daq = Arduino_SoftTiming.auto_connect()
    daq.pwm_pulse(3, 5, 0.05, blocking=False)
    daq.pwm_pulse(9, 5, 0.5, blocking=True)
    daq.close()