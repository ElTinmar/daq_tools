from daq_tools import Arduino_SoftTiming

daq = Arduino_SoftTiming.auto_connect()
daq.pwm_pulse(3, 5, 0.05, blocking=False)
daq.pwm_pulse(9, 5, 0.5, blocking=True)
daq.close()