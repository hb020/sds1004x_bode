"""
Driver for the Agilent 33500B series Function Generator via LXI
by igorus512 (igorus@mail.ru)

The 33522B has the following parameters:
- 2 channels
- fixed output impedance of 50 Ohm
- freq 1 uHz to 30 MHz (sine, square and pulse waveforms)
- freq 1 uHz to 200 kHz (triangle and ramp waveforms)
- amp 10 Vpp

The 33500B/33600A series has other models with different parameters, but the driver should work for all of them with minor adjustments.
Some have 1 channel only, and some go up to 120 MHz.

Driver uses LAN connectivity from the intermediate PC to the AWG 
(btw AWG also has GPIB and USB interfaces available).
"""

import time
from .base_awg import BaseAWG
from . import constants
import pyvisa as visa
from .exceptions import UnknownChannelError

# GPIB interface settings
# TIMEOUT = 5000  # milliseconds
TIMEOUT = 10000  # milliseconds

# Wave type mapping: our constants -> 33522B commands
# SINusoid|SQUare|TRIangle|RAMP
WAVE_TYPE_MAP = {
    constants.SINE: "SIN",
    constants.SQUARE: "SQU",
    constants.TRIANGLE: "TRI",
    constants.PULSE: "RAMP",
}

# Output impedance 50 ohm. This is fixed.
R_OUT = 50.0

# If you have a 33500B/33600A model with different parameters (e.g. only 1 channel, or lower max frequency), you can adjust the following values accordingly.
# This is not required, as it is only for bounds checking. You should have set the scope's bode plot configuration to be compatible with the instrument's capabilities.
NR_CHANNELS = 2
MIN_FREQ = 0.001
MAX_FREQ = 120e6
ENABLE_ERROR_CHECKING = False  # Set to True to enable error checking after each command (for safer execution, but slower)


class AG33500B(BaseAWG):
    SHORT_NAME = "ag33500b"

    """
    Agilent 33500B/33600A Function Generator driver.
    Supports:
    - Frequency: 0.001 Hz to 120 MHz
    - Waveforms: sine, square, triangle, pulse, ramp
    - Amplitude: 0.1 V to 10 V peak
    - Offset: -10 V to +10 V
    - Double channel output
    """

    def __init__(self, port: str = "", baud_rate: int = 0, 
                 timeout: int = TIMEOUT, log_debug: bool = False, 
                 force_pyvisa_py: bool = False):
        """
        port: AWG connection string.
        baud_rate: Ignored.
        timeout: GPIB timeout in milliseconds
        log_debug: Enable debug logging
        """
        super().__init__(log_debug=log_debug, force_pyvisa_py=force_pyvisa_py)
        self.printdebug("init")
        self.port = port
        self.rm = None
        self.m = None
        self.timeout = timeout
        self.channel_on = [False, False]
        # State tracking
        self.current_wave_type = constants.SINE
        self.load_impedance = 50.0
    
    def _connect(self):
        if self.m is not None:
            return
            
        try:
            # Create LXI connection via connection string
            self.printdebug(f"Connecting to '{self.port}'...")
            self.rm = visa.ResourceManager("@py" if self.force_pyvisa_py else "")
            self.m = self.rm.open_resource(self.port)
            self.m.timeout = self.timeout * 1000
            self.printdebug(f"Connected to '{self.port}' successfully.")
        except Exception as e:
            self.printdebug(f"Connection failed: {e}")
            raise

    def disconnect(self):
        self.printdebug("Disconnecting...")
        try:
            if self.m is not None:
                self.enable_output(0, False)
                self.m.close()
            if self.rm is not None:
                self.rm.close()
        except Exception as e:
            self.printdebug(f"Disconnect error: {e}")
        finally:
            self.printdebug("Disconnected.")
            self.m = None
            self.rm = None

    def _send_command(self, cmd: str) -> bool:
        """Send a command to the instrument."""
        self._connect()
        self.printdebug(f"Command: {cmd}")
        self.m.write(cmd)
        time.sleep(0.1)  # Small delay between commands
        if ENABLE_ERROR_CHECKING:
            r = self.m.query(":SYSTem:ERRor?")
            if r.startswith("0,"):
                return True
            else:
                print(f"ERR: command \"{cmd}\" returned {r}")
                # raise some error maybe
                return False
        else:
            return True

    def _query_command(self, cmd: str) -> str:
        """Send a query command and return the response."""
        self._connect()
        self.printdebug(f"Query: {cmd}")
        response = self.m.query(cmd)
        return response.strip()

    def initialize(self):
        """Initialize the instrument."""
        self.printdebug("initialize")
        self._connect()
        
        # Reset to default state
        self._send_command("*RST")
        time.sleep(0.5)
        
        # Disable output initially, set waveform to sin
        self.enable_output(1, False)
        self.set_wave_type(1, constants.SINE)
        if NR_CHANNELS > 1:
            self.enable_output(2, False)
            self.set_wave_type(2, constants.SINE)
        
        # Clear any previous errors
        self._send_command("*CLS")

    def get_id(self) -> str:
        """Query device identification."""
        try:
            id_string = self._query_command("*IDN?")
            return id_string
        except Exception as e:
            self.printdebug(f"ID query error: {e}")
            return "Agilent 33500B/33600A (unknown state)"

    def enable_output(self, channel: int, on: bool):
        """
        Enable or disable output.
        Args:
            channel: Channel number (1/2, 0 = both)
            on: True to enable, False to disable
        """
        self.printdebug(f"enable_output(channel: {channel}, on: {on})")
        if (channel < 0) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2, or 0 for both")
        
        if channel == 0:
            self.enable_output(1, on)
            if NR_CHANNELS > 1:
                self.enable_output(2, on)

        if channel == 1:
            cmd = "OUTP1 ON" if on else "OUTP1 OFF"
            self._send_command(cmd)

        if channel == 2:
            cmd = "OUTP2 ON" if on else "OUTP2 OFF"
            self._send_command(cmd)

    def set_frequency(self, channel: int, freq: float):
        """
        Set output frequency.
        Args:
            channel: Channel number (1/2)
            freq: Frequency in Hz (0.001 Hz to 120 MHz)
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq: {freq} Hz)")

        if (channel < 1) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2")
        
        if (freq < MIN_FREQ) or (freq > MAX_FREQ):
            raise ValueError(f"Frequency {freq} Hz is out of range ({MIN_FREQ} Hz to {MAX_FREQ} Hz)")
        
        if channel == 1:
            cmd = f"SOUR1:FREQ {freq}"

        if channel == 2:
            cmd = f"SOUR2:FREQ {freq}"
        
        self._send_command(cmd)

    def set_phase(self, channel: int, phase: float):
        """
        Set output phase.
        Args:
            channel: Channel number (1/2)
            phase: Phase in degrees (0)
        """
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase}°)")
        
        if (channel < 1) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2")
        
        # Normalize phase to 0-360 range
        phase = phase % 360
        self.printdebug(f"Normalized phase: {phase}°)")
        
        if channel == 1:
            cmd = f"SOUR1:PHAS {phase}"

        if channel == 2:
            cmd = f"SOUR2:PHAS {phase}"
        
        self._send_command(cmd)

    def set_wave_type(self, channel: int, wave_type: int):
        """
        Set output waveform type.
        Args:
            channel: Channel number (1/2)
            wave_type: Waveform type (SINE, SQUARE, TRIANGLE, PULSE from constants)
        """
        self.printdebug(f"set_wave_type(channel: {channel}, wave_type: {wave_type})")
        
        if (channel < 1) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2")
        
        if wave_type not in WAVE_TYPE_MAP:
            raise ValueError(f"Unsupported waveform type: {wave_type}")
        
        self.current_wave_type = wave_type
        wave_cmd = WAVE_TYPE_MAP[wave_type]
        
        if channel == 1:
            cmd = f"SOUR1:FUNC {wave_cmd}"

        if channel == 2:
            cmd = f"SOUR2:FUNC {wave_cmd}"
        
        self._send_command(cmd)

    def set_amplitude(self, channel: int, amplitude: float):
        """
        Set output amplitude (peak-to-peak voltage).
        Args:
            channel: Channel number (1/2)
            amplitude: Amplitude in volts (0.1 V to 10 V peak)
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude: {amplitude} V)")
        
        if (channel < 1) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2")
        
        if amplitude < 0.1 or amplitude > 10:
            raise ValueError(f"Amplitude {amplitude} V is out of range (0.1 V to 10 V peak)")
        
        if channel == 1:
            cmd = f"SOUR1:VOLT {amplitude} Vpp"

        if channel == 2:
            cmd = f"SOUR2:VOLT {amplitude} Vpp"
       
        self._send_command(cmd)

    def set_offset(self, channel: int, offset: float):
        """
        Set DC offset voltage.
        Args:
            channel: Channel number (1/2)
            offset: Offset voltage in volts (-5 V to +5 V)
        """
        self.printdebug(f"set_offset(channel: {channel}, offset: {offset} V)")
        
        if (channel < 1) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2")
        
        if offset < -5 or offset > 5:
            raise ValueError(f"Offset {offset} V is out of range (-5 V to +5 V)")
        
        if channel == 1:
            cmd = f"SOUR1:VOLT:OFFS {offset}"

        if channel == 2:
            cmd = f"SOUR2:VOLT:OFFS {offset}"
       
        self._send_command(cmd)

    def set_load_impedance(self, channel: int, z: float):
        """
        Set load impedance (just for info).
        The 33500B/33600A has a fixed 50 ohm output impedance.
        This method stores the load impedance value for reference 
        but doesn't actually change the hardware setting.
        Args:
            channel: Channel number (1/2)
            z: Load impedance in ohms (use constants.HI_Z for high impedance)
        """
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance: {z})")
        
        if (channel < 1) or (channel > NR_CHANNELS):
            if NR_CHANNELS == 1:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1")
            else:
                raise UnknownChannelError("Channel number for 33500B/33600A should be 1 or 2")
        
        # Store for reference - 33500B/33600A output impedance is fixed at 50 ohms
        if z == constants.HI_Z or z == float("inf"):
            self.load_impedance = float("inf")
        else:
            self.load_impedance = z
        
        # Note: 33500B/33600A output impedance is fixed, cannot be changed via software
        self.printdebug(f"Load impedance set to {z} (stored for reference only)")


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
