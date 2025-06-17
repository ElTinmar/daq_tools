import nidaqmx

system = nidaqmx.system.System.local()
for dev in system.devices:
    print(dev.name)

# analog read single point / two channels
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai1", min_val=-10.0, max_val=10.0)
    data = task.read()

# analog read multiple points
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("NIPCI-6110/ai0", min_val=-10.0, max_val=10.0)
    data = task.read(number_of_samples_per_channel=1000)
     
# analog write
with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
    task.write([1.1, 2.2, 3.3, 4.4, 5.5], auto_start=True)