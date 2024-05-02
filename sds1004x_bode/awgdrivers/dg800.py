'''
Created on May 1, 2024

@author: hb020
'''

from .base_awg import BaseAWG
from . import constants
import pyvisa as visa
from .exceptions import UnknownChannelError

TIMEOUT = 5

DEBUG_OUT = False

CHANNELS = (0, 1, 2)
CHANNELS_ERROR = "DG800 has only 2 channels."
WAVEFORM_COMMANDS = {
    constants.SINE: ":SOURCE{channel}:FUNC SIN",
    constants.SQUARE: ":SOURCE{channel}:FUNC SQU",
    constants.PULSE: ":SOURCE{channel}:FUNC PULSE",
    constants.TRIANGLE: ":SOURCE{channel}:FUNC TRIANG"
    }

# Default AWG settings
DEFAULT_LOAD = 50
DEFAULT_OUTPUT_ON = False


class RigolDG800(BaseAWG):
    '''
    DG800 waveform generator driver.
    '''

    SHORT_NAME = "dg800"

    def __init__(self, port, ignore=None, timeout=TIMEOUT):
        if DEBUG_OUT:
            print("DG800: init")
        self.port = port
        self.rm = None
        self.m = None
        self.timeout = timeout
        self.channel_on = [False, False]
        self.r_load = [DEFAULT_LOAD, DEFAULT_LOAD]
        self.v_out_coeff = [1, 1]

    def send_command(self, cmd):
        self.m.write(cmd)
        r = self.m.query(":SYSTem:ERRor?")
        if r.startswith("0,"):
            return True
        else:
            print(f"ERR: command \"{cmd}\" returned {r}")
            # raise some error maybe
            return False

    def connect(self):
        if DEBUG_OUT:
            print("DG800: connect")
        self.rm = visa.ResourceManager()
        self.m = self.rm.open_resource(self.port)
        self.m.timeout = self.timeout * 1000

    def disconnect(self):
        if DEBUG_OUT:
            print("DG800: disconnect")
        if self.m is not None:
            self.enable_output(0, False)
            self.m.close()
            self.m = None
        if self.rm is not None:
            self.rm.close()
            self.rm = None

    def initialize(self):
        if DEBUG_OUT:
            print("DG800: initialize")
        self.connect()
        self.m.write("*CLS")
        # self.m.write("*RST")

    def get_id(self):
        ans = self.m.query("*IDN?")
        return ans.strip()

    def enable_output(self, channel, on):
        if DEBUG_OUT:
            print(f"DG800: enable_output(channel: {channel}, on:{on})")
            
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel == 0:
            self.enable_output(1, on)
            self.enable_output(2, on)
        else:
            self.channel_on[channel - 1] = on        
            self.send_command(f":OUTPUT{channel}:STATE {"ON" if on else "OFF"}")

    def set_frequency(self, channel, freq):
        if DEBUG_OUT:
            print(f"DG800: set_frequency(channel: {channel}, freq:{freq})")
            
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel == 0:
            self.set_frequency(1, freq)
            self.set_frequency(2, freq)
        else:
            self.send_command(f":SOURCE{channel}:FREQ {freq:.10f}")        
        
    def set_phase(self, channel, phase):
        if DEBUG_OUT:
            print(f"DG800: set_phase(phase: {phase})")
        # phase settings do not really work on this device, but I try anyway
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel == 0:
            self.set_frequency(1, phase)
            self.set_frequency(2, phase)
        else:
            try:
                phase = int(phase)
            except:
                phase = 0
            # Allow phase to wrap below 0
            if phase < 0:
                phase += 360
            # but if still off, use defaults
            if phase < 0:
                phase = 0
            if phase > 360:
                phase = 0
            self.send_command(f":SOURCE{channel}:PHASE {phase}")            

    def set_wave_type(self, channel, wave_type):
        if DEBUG_OUT:
            print(f"DG800: set_wave_type(channel: {channel}, wavetype:{wave_type})")
        
        if wave_type not in constants.WAVE_TYPES:
            raise ValueError("Incorrect wave type.")
        
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)        
        if channel == 0:
            self.set_wave_type(1, wave_type)
            self.set_wave_type(2, wave_type)
        else:        
            cmd = WAVEFORM_COMMANDS[wave_type]
            cmd = cmd.replace("{channel}", str(channel))
            self.send_command(cmd)            

    def set_amplitude(self, channel, amp):
        if DEBUG_OUT:
            print(f"DG800: set_amplitude(channel: {channel}, amplitude:{amp})")
            
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel == 0:
            self.set_amplitude(1, amp)
            self.set_amplitude(2, amp)
        else:     
            # Adjust the amplitude to the defined load impedance
            amp = amp / self.v_out_coeff[channel - 1]
            self.send_command(f":SOURCE{channel}:VOLT:AMPL {amp:.3f}")            

    def set_offset(self, channel, offset):
        if DEBUG_OUT:
            print(f"DG800: set_offset(channel: {channel}, offset:{offset})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel == 0:
            self.set_offset(1, offset)
            self.set_offset(2, offset)
        else:               
            # Adjust the offset to the defined load impedance
            offset = offset / self.v_out_coeff[channel - 1] 
            self.send_command(f":SOURCE{channel}:VOLT:OFFS {offset}")               

    def set_load_impedance(self, channel, z):
        if DEBUG_OUT:
            print(f"DG800: set_load_impedance(channel: {channel}, impedance:{z})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel == 0:
            self.set_load_impedance(1, z)
            self.set_load_impedance(2, z)
        else:                
            if z == constants.HI_Z:
                v_out_coeff = 1
            else:
                v_out_coeff = z / (z + (DEFAULT_LOAD * 1.0))
            self.v_out_coeff[channel - 1] = v_out_coeff      
            self.send_command(f":OUTPUT{channel}:IMP {z}")      

