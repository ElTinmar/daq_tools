from daq_tools import LabJackU3_SoftTiming
import time
import logging

DURATION_SEC = 10
FREQUENCY_HZ = 20

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    with LabJackU3_SoftTiming.auto_connect() as daq:

        for j in range(DURATION_SEC):
            for i in range(FREQUENCY_HZ):
                daq.digital_write(0, True)
                time.sleep(0.45*1/FREQUENCY_HZ)
                daq.digital_write(2, True)
                time.sleep(0.05 * 1/FREQUENCY_HZ)
                daq.digital_write(0, False)
                time.sleep(0.05 * 1/FREQUENCY_HZ)
                daq.digital_write(2, False)
                time.sleep(0.45 * 1/FREQUENCY_HZ)

