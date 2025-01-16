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

# Here is the section you may want to change -- START
# Adapt this to the AWG and port you use.

# set MY_AWG to the driver name you want to test. example: "fy6600" or "dummy"
# set MY_AWG to None if you want to tests all AWGs. That is nice for code debugging, but may not be what you want.
MY_AWG = "dummy"

# Default port and baud:
DEFAULT_PORT = "/dev/tty.usbserial-FTHJGC2Z"
DEFAULT_BAUD = None

# If you have multiple AWGs to test, you can also adapt `config`:
config = {"bk4075": {"baud": 19200},
          "dg800": {"port": "TCPIP::192.168.007.204::INSTR"},
          "utg1000x": {"port": "TCPIP::192.168.007.204::INSTR"}
          }

# if you want to "single step" the tool, ("Press Enter to continue...") , then set this to False
RUN_UNINTERRUPTED = True

# Here is the section you may want to change -- END


def get_go_for_next_step():
    if not RUN_UNINTERRUPTED:        
        input("Press Enter to continue...")


def test_awg(awg_name):
    # test one AWG
    
    # Default settings
    port = DEFAULT_PORT
    baud = DEFAULT_BAUD
    if awg_name in config:
        my_config = config[awg_name]
        if "port" in my_config:
            port = my_config["port"]
        if "baud" in my_config:
            baud = my_config["baud"]
            
    print(f"\n=====================\nTesting AWG \"{awg_name}\"\n=====================")
    try:
        awg_class = awg_factory.get_class_by_name(awg_name)

        awg = awg_class(port=port, baud_rate=baud, timeout=TIMEOUT, log_debug=True)
        awg.initialize()

        # Get AWG id
        awg_id = awg.get_id()
        print(f"AWG id: {awg_id}")

        # Output off
        print("Setting output to off of all channels.")
        awg.enable_output(0, False)
        get_go_for_next_step()

        # Channel 1: 7257.86Hz, 0.722Vpp, offset 0.041V
        print("Setting CH 1 output on.")
        awg.enable_output(1, True)        
        get_go_for_next_step()
        print("Setting CH 1 Wave form to Sine wave")
        awg.set_wave_type(1, constants.SINE)
        get_go_for_next_step()
        print("Setting CH 1 Frequency: 7257.865243Hz")
        awg.set_frequency(1, 7257.865243)
        get_go_for_next_step()
        print("Setting CH 1 Phase: 0")
        awg.set_phase(1, 0)
        get_go_for_next_step()
        print("Setting CH 1 Impedance: 50 Ohm")
        awg.set_load_impedance(1, 50)
        get_go_for_next_step()
        print("Setting CH 1 Amplitude: 0.722Vpp, which should become 1.444Vpp on the output")
        awg.set_amplitude(1, 0.722)
        get_go_for_next_step()
        print("Setting CH 1 Offset: 41mVdc, which should become 82mVdc on the output")
        awg.set_offset(1, 0.041)
        get_go_for_next_step()

        try:
            # Channel 2: 35564.0493Hz, 1.5Vpp, offset -0.35V
            print("Setting CH 2 output on.")
            awg.enable_output(2, True)        
            get_go_for_next_step()
            print("Setting CH 2 Wave form to Sine wave")
            awg.set_wave_type(2, constants.SINE)
            get_go_for_next_step()
            print("Setting CH 2 Frequency: 35564.0493Hz")
            awg.set_frequency(2, 35564.0493)
            get_go_for_next_step()
            print("Setting CH 2 Phase: 0")
            awg.set_phase(2, 0)
            get_go_for_next_step()
            print("Setting CH 2 Impedance: HiZ")
            awg.set_load_impedance(2, constants.HI_Z)
            get_go_for_next_step()
            print("Setting CH 2 Amplitude: 1.5Vpp")
            awg.set_amplitude(2, 1.5)
            get_go_for_next_step()
            print("Setting CH 2 Offset: -0.35Vdc")
            awg.set_offset(2, -0.35)
            get_go_for_next_step()
        except UnknownChannelError:
            print("This AWG doesn't have second channel.")

        # Output on
        print("Setting output to on on all channels.")
        awg.enable_output(0, True)

        # Disconnect
        print("Disconnecting from the AWG.")
        awg.disconnect()
    except Exception as e:
        print(f"FAILED. Exception: {e}")
        

if __name__ == '__main__':

    my_awg = MY_AWG
    
    if my_awg is None:
        # This tests all AWGs
        for awg_name in awg_factory.get_names():
            test_awg(awg_name)
    else:
        test_awg(my_awg)
    
