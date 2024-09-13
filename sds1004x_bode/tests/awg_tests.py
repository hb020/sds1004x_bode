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

    # default values
    baud = None
    # port = "/dev/ttyUSB0"
    # port = "/dev/tty.usbserial-FTHJGC2Z"
        
    # awg_name = "dummy"

    # awg_name = "jds6600"
    # port = "/dev/ttyUSB0"

    # awg_name = "fy6600"
    # port = "/dev/ttyUSB0"
    
    # awg_name = "fy"
    # port = "/dev/ttyUSB0"
    
    # awg_name = "ad9910"
    # port = "/dev/ttyUSB0"        

    # awg_name = "bk4075"
    # port = "/dev/ttyUSB0"
    # baud = 19200
    
    awg_name = "dg800"
    # awg_name = "utg1000x"
    port = "TCPIP::192.168.007.204::INSTR"
    
    awg_class = awg_factory.get_class_by_name(awg_name)

    awg = awg_class(port, baud, TIMEOUT)
    awg.initialize()

    # Get AWG id
    awg_id = awg.get_id()
    print(f"AWG id: {awg_id}")

    # Output off
    print("Setting output to off of all channels.")
    awg.enable_output(0, False)

    # Channel 1: 7257.86Hz, 0.722Vpp, offset 0.041V
    print("Setting CH 1 Wave form to Sine wave")
    awg.set_wave_type(1, constants.SINE)
    print("Setting CH 1 Frequency: 7257.865243Hz")
    awg.set_frequency(1, 7257.865243)
    print("Setting CH 1 Phase: 0")
    awg.set_phase(1, 0)
    print("Setting CH 1 Impedance: 50 Ohm")
    awg.set_load_impedance(1, 50)
    print("Setting CH 1 Amplitude: 0.722Vpp, which should become 1.444Vpp on the output")
    awg.set_amplitude(1, 0.722)
    print("Setting CH 1 Offset: 41mVdc, which should become 82mVdc on the output")
    awg.set_offset(1, 0.041)

    try:
        # Channel 2: 35564.0493Hz, 1.5Vpp, offset -0.35V
        print("Setting CH 2 Wave form to Sine wave")
        awg.set_wave_type(2, constants.SINE)
        print("Setting CH 2 Frequency: 35564.0493Hz")
        awg.set_frequency(2, 35564.0493)
        print("Setting CH 2 Phase: 0")
        awg.set_phase(2, 0)
        print("Setting CH 2 Impedance: HiZ")
        awg.set_load_impedance(2, constants.HI_Z)
        print("Setting CH 2 Amplitude: 1.5Vpp")
        awg.set_amplitude(2, 1.5)
        print("Setting CH 2 Offset: -0.35Vdc")
        awg.set_offset(2, -0.35)
    except UnknownChannelError:
        print("This AWG doesn't have second channel.")

    # Output on
    print("Setting output to on on all channels.")
    awg.enable_output(0, True)

    # Disconnect
    print("Disconnecting from the AWG.")
    awg.disconnect()
