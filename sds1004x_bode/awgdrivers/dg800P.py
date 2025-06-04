'''
Created on June 3, 2025

@author: JohnKr
'''

from .base_awg import BaseAWG
from . import constants
import pyvisa as visa
from .exceptions import UnknownChannelError

TIMEOUT = 5

CHANNELS = (0, 1, 2)
MYNAME = "DG800P"
CHANNELS_ERROR = f"{MYNAME} has only 2 channels."
WAVEFORM_COMMANDS = {
    constants.SINE: ":SOURCE{channel}:FUNC SIN",
    constants.SQUARE: ":SOURCE{channel}:FUNC SQU",
    constants.PULSE: ":SOURCE{channel}:FUNC PULSE",
    constants.TRIANGLE: ":SOURCE{channel}:FUNC TRIANG"
}

# Default AWG settings
DEFAULT_LOAD = 50
DEFAULT_OUTPUT_ON = False


class RigolDG800P(BaseAWG):
    '''
    DG800/DG900 Pro waveform generator driver.
    '''

    SHORT_NAME = "dg800p"

    def __init__(self, port: str = "", baud_rate: int = None, timeout: int = TIMEOUT, log_debug: bool = False):
        """baud_rate parameter is ignored."""
        super().__init__(log_debug=log_debug)
        self.printdebug("init")
        self.port = port
        self.rm = None
        self.m = None
        self.timeout = timeout
        self.channel_on = [False, False]

    def _send_command(self, cmd):
        # local function to send a command and check for errors
        self.printdebug(f"send command \"{cmd}\"")
        self.m.write(cmd)
        r = self.m.query(":SYSTem:ERRor?")
        if r.startswith("0,"):
            return True
        else:
            print(f"ERR: command \"{cmd}\" returned {r}")
            # raise some error maybe
            return False

    def _connect(self):
        self.rm = visa.ResourceManager()
        self.m = self.rm.open_resource(self.port)
        self.m.timeout = self.timeout * 1000

    def disconnect(self):
        self.printdebug("disconnect")
        if self.m is not None:
            self.enable_output(0, False)
            self.m.close()
            self.m = None
        if self.rm is not None:
            self.rm.close()
            self.rm = None

    def initialize(self):
        self.printdebug("initialize")
        self._connect()
        self.m.write("*CLS")
        # self.m.write("*RST")

    def get_id(self) -> str:
        ans = self.m.query("*IDN?")
        return ans.strip()

    def enable_output(self, channel: int, on: bool):
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.enable_output(1, on)
            self.enable_output(2, on)
        else:
            self.channel_on[channel - 1] = on
            self._send_command(f":OUTPUT{channel}:STATE {'ON' if on else 'OFF'}")

    def set_frequency(self, channel: int, freq: float):
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_frequency(1, freq)
            self.set_frequency(2, freq)
        else:
            self._send_command(f":SOURCE{channel}:FREQ {freq:.10f}")        

    def set_phase(self, channel: int, phase: float):
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase})")
        # phase settings do not really work on this device, but I try anyway
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_phase(1, phase)
            self.set_phase(2, phase)
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
            self._send_command(f":SOURCE{channel}:PHASE {phase}")

    def set_wave_type(self, channel: int, wave_type: int):
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type})")

        if wave_type not in constants.WAVE_TYPES:
            raise ValueError("Incorrect wave type.")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_wave_type(1, wave_type)
            self.set_wave_type(2, wave_type)
        else:
            cmd = WAVEFORM_COMMANDS[wave_type]
            cmd = cmd.replace("{channel}", str(channel))
            self._send_command(cmd)

    def set_amplitude(self, channel: int, amplitude: float):
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_amplitude(1, amplitude)
            self.set_amplitude(2, amplitude)
        else:
            # For Rigols it is not necessary to adjust the amplitude to the defined load impedance
            # amplitude = amplitude / self.v_out_coeff[channel - 1]
            # SDS1000X HD sends always the voltage as VPP, even if set to VRMS in the Bode plot setup of the scope
            # Rigols interpret the amplitude to have the unit that was used by the last manual entry or the last UNIT command
            self._send_command(f":SOURCE{channel}:VOLT:UNIT VPP") 
            self._send_command(f":SOURCE{channel}:VOLT {amplitude:.3f}")

    def set_offset(self, channel: int, offset: float):
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_offset(1, offset)
            self.set_offset(2, offset)
        else:
            self._send_command(f":SOURCE{channel}:VOLT:OFFS {offset}")

    def set_load_impedance(self, channel: int, z: float):
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_load_impedance(1, z)
            self.set_load_impedance(2, z)
        else:
            # The maximum load impedance that can be defined in a Rigol is 10kOhms
            # The current Bode implementation on the Siglent scope allows for values
            # of 50, 75, 600, Hi-Z. But the scope actually sends a value of 1MOhms (1000000)
            # when setting the load impedance to Hi-Z. The Rigol refuses this setting and
            # sets 10KOhms instead. With this we force it to Hi-Z.
            if z > 10000:
                z = "INF"
            self._send_command(f":OUTPUT{channel}:LOAD {z}")


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
