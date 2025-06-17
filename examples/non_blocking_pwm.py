from daq_tools import Arduino_DAQ

daq = Arduino_DAQ.auto_connect()
daq.pwm_pulse(3, 5, 0.05, blocking=False)
daq.pwm_pulse(9, 5, 0.5, blocking=True)
daq.close()