from distutils.core import setup

setup(
    name='daq_tools',
    python_requires='>=3.8',
    author='Martin Privat',
    version='0.1.16',
    packages=['daq_tools'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='control software and hardware timed DAQ',
    long_description=open('README.md').read(),
    install_requires=[
        "labjackpython",
        "pyfirmata",
        "pyserial",
        "nidaqmx"
    ]
)