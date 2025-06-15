from distutils.core import setup

setup(
    name='ZebVR',
    python_requires='>=3.8',
    author='Martin Privat',
    version='0.1.0',
    packages=['ZebVR'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    description='Open and closed-loop virtual reality',
    long_description=open('README.md').read(),
    install_requires=[
        "labjackpython",
        "pyfirmata"
    ]
)