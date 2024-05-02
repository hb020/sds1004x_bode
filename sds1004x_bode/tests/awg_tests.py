'''
Created on June 1, 2018

@author: 4x1md

@summary: Tester module which tests AWG drivers.
'''

# stuff needed to get the modules from the parent directory
import sys
sys.path.insert(0, '..')

from awgdrivers.exceptions import UnknownChannelError
from awgdrivers import constants
from awg_factory import awg_factory

# Port settings constants
TIMEOUT = 5

if __name__ == '__main__':

    # awg_name = "dummy"
    # port = None
    # baud = None

    # awg_name = "jds6600"
    # port = "/dev/ttyUSB0"
    # baud = 115200

    # awg_name = "fy6600"
    # port = "/dev/ttyUSB0"
    # baud = 19200

    # awg_name = "bk4075"
    # port = "/dev/ttyUSB0"
    # baud = 19200
    
    awg_name = "dg800"
    port = "TCPIP::192.168.007.204::INSTR"
    baud = None
    
    awg_class = awg_factory.get_class_by_name(awg_name)

    awg = awg_class(port, baud, TIMEOUT)
    awg.initialize()

    # Get AWG id
    awg_id = awg.get_id()
    print(f"AWG id: {awg_id}")

    # Output off
    print("Setting output to off.")
    awg.enable_output(0, False)

    # Channel 1: 257.86Hz, 1Vpp, offset 0.5V
    awg.set_wave_type(1, constants.SINE)
    awg.set_frequency(1, 7257.865243)
    awg.set_load_impedance(1, 50)
    awg.set_amplitude(1, 0.722)
    awg.set_offset(1, 0.041)

    try:
        # Channel 2: 35564.0493Hz, 1.5Vpp, offset -0.35V
        awg.set_wave_type(2, constants.SINE)
        awg.set_frequency(2, 35564.0493)
        awg.set_load_impedance(2, constants.HI_Z)
        awg.set_amplitude(2, 1.5)
        awg.set_offset(2, -0.35)
    except UnknownChannelError:
        print("This AWG doesn't have second channel.")

    # Output on
    print("Setting output to on.")
    awg.enable_output(0, True)

    # Disconnect
    print("Disconnecting from the AWG.")
    awg.disconnect()
