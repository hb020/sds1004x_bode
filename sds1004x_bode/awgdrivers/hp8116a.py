"""
Driver for HP 8116A Pulse/Function Generator using HPIB (GPIB) interface.

The HP8116A is a versatile function generator supporting frequencies from 
0.01 Hz to 50 MHz with sine, square, triangle, pulse, and ramp waveforms.
Communication uses HPIB (Hewlett-Packard Interface Bus / GPIB / IEEE 488).

Requires pyvisa and a GPIB interface adapter (e.g., National Instruments GPIB-USB-HS)
"""

import pyvisa
import time
from .base_awg import BaseAWG
from . import constants
from .exceptions import UnknownChannelError

# GPIB interface settings
TIMEOUT = 5000  # milliseconds
# DEFAULT_GPIB_ADDRESS = 16  # Default GPIB address for HP8116A

# Wave type mapping: our constants -> HP8116A commands
WAVE_TYPE_MAP = {
    constants.SINE: "W1",
    constants.SQUARE: "W2",
    constants.TRIANGLE: "W3",
    constants.PULSE: "W4",
}

# Output impedance of the HP8116A
R_OUT = 50.0  # 50 ohm output impedance


class HP8116A(BaseAWG):
    """
    HP 8116A Pulse/Function Generator driver.
    
    Supports:
    - Frequency: 0.01 Hz to 50 MHz
    - Waveforms: sine, square, triangle, pulse, ramp
    - Amplitude: 0.1 V to 20 V peak
    - Offset: -10 V to +10 V
    - Single channel output
    """
    SHORT_NAME = "hp8116a"

    def __init__(self, port: str, 
                 baud_rate: int = 0, timeout: int = TIMEOUT, 
                 log_debug: bool = False, force_pyvisa_py: bool = False):
        """
        Initialize HP8116A driver.
        Args:
            port: either an instrument address, or a VISA string.
            it is defaulted by the variable 
                DEFAULT_PORT = "xx" 
            in the bode.py file. 
            baud_rate: Ignored (kept for compatibility with other drivers)
            timeout: GPIB timeout in milliseconds
            log_debug: Enable debug logging
        """
        super().__init__(log_debug=log_debug, force_pyvisa_py=force_pyvisa_py)
        self.printdebug("init")
        self.port = port
        self.timeout = timeout
        self.instrument = None
        self.resource_manager = None
        
        # State tracking
        self.current_wave_type = constants.SINE
        self.output_enabled = False
        self.load_impedance = 50.0
        
    def _get_gpib_address_string(self) -> str:
        """
        Generate GPIB address string for pyvisa.        
        Accepts port in two formats:
        - Integer (1-30) or numeric string ("1"-"30"): converts to GPIB0::N::INSTR
        - Full VISA string (e.g., "GPIB0::16::INSTR"): returns as-is after validation
        Returns:
            str: Valid VISA resource string for pyvisa
        Raises:
            ValueError: If port value is invalid
            TypeError: If port is not int or str
        """
        # Handle integer port number
        if self.port.isdigit():                         # is it an integer?
            if 1 <= int(self.port) <= 30:               # is it between 1 and 30?   
                return f"GPIB0::{self.port}::INSTR"     # format connection string
            else:
                raise ValueError(f"GPIB address must be between 1-30, got {self.port}")    
        # Check if it's already a VISA resource string
        elif "::" in self.port:  # does it look like a VISA string?
            return self.port  # if so, return as-is 
        else:
            raise TypeError(f"Invalid port format: '{self.port}'. Expected number (1-30) or VISA string (like GPIB0::N::INSTR or TCPIP::ip_address::gpib,N::INSTR). You can also adapt the DEFAULT_PORT in bode.py")

    def _connect(self):
        """Establish GPIB connection to the instrument."""
        if self.instrument is not None:
            return
            
        try:
            self.resource_manager = pyvisa.ResourceManager("@py" if self.force_pyvisa_py else "")
            gpib_addr = self._get_gpib_address_string()
            self.printdebug(f"Connecting to '{gpib_addr}'")
            
            self.instrument = self.resource_manager.open_resource(gpib_addr)
            self.instrument.timeout = self.timeout
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            
            self.printdebug(f"Connected to '{gpib_addr}' successfully")
        except Exception as e:
            self.printdebug(f"Connection failed: {e}")
            raise

    def disconnect(self):
        """Close GPIB connection."""
        self.printdebug("disconnect")
        if self.instrument is not None:
            try:
                self.instrument.close()
            except Exception as e:
                self.printdebug(f"Disconnect error: {e}")
            finally:
                self.instrument = None
                
        if self.resource_manager is not None:
            try:
                self.resource_manager.close()
            except Exception as e:
                self.printdebug(f"Resource manager close error: {e}")
            finally:
                self.resource_manager = None

    def _send_command(self, cmd: str):
        """Send a command to the instrument."""
        self._connect()
        self.printdebug(f"Command: {cmd}")
        self.instrument.write(cmd)
        time.sleep(0.1)  # Small delay between commands

    def _query_command(self, cmd: str) -> str:
        """Send a query command and return the response."""
        self._connect()
        self.printdebug(f"Query: {cmd}")
        response = self.instrument.query(cmd)
        return response.strip()

    def initialize(self):
        """Initialize the instrument."""
        self.printdebug("initialize")
        self._connect()
        
        # Reset to default state
        self._send_command("DCL")
        time.sleep(0.5)
        
        # Disable output initially
        self.enable_output(1, False)
        
        # Set default waveform to sine
        self.set_wave_type(1, constants.SINE)
        
        # Clear any previous errors
        self._send_command("SDC")

    def get_id(self) -> str:
        """Query device identification."""
        try:
            id_string = self._query_command("*IDN?")
            return id_string
        except Exception as e:
            self.printdebug(f"ID query error: {e}")
            return "HP8116A (unknown)"

    def enable_output(self, channel: int, on: bool):
        """
        Enable or disable output.
        
        Args:
            channel: Channel number (1 for HP8116A, single channel device)
            on: True to enable, False to disable
        """
        self.printdebug(f"enable_output(channel: {channel}, on: {on})")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        self.output_enabled = on
        cmd = "D0" if on else "D1"
        self._send_command(cmd)

    def set_frequency(self, channel: int, freq: float):
        """
        Set output frequency.
        
        Args:
            channel: Channel number (1 for HP8116A)
            freq: Frequency in Hz (0.01 Hz to 50 MHz)
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq: {freq} Hz)")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        if freq < 0.01 or freq > 50e6:
            raise ValueError(f"Frequency {freq} Hz is out of range (0.01 Hz to 50 MHz)")
        
        # HP8116A uses FRQ command (in Hz)
        cmd = f"FRQ {freq} HZ"
        self._send_command(cmd)

    def set_phase(self, channel: int, phase: float):
        """
        Set output phase to zero (HP8116A does not support phase adjustment).
        
        Args:
            channel: Channel number (1 for HP8116A)
            phase: Phase in degrees (0)
        """
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase}°)")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        # Normalize phase to 0-360 range
        phase = phase % 360
        
        # HP8116A uses PHAS command
        cmd = "H0"
        self._send_command(cmd)

    def set_wave_type(self, channel: int, wave_type: int):
        """
        Set output waveform type.
        
        Args:
            channel: Channel number (1 for HP8116A)
            wave_type: Waveform type (SINE, SQUARE, TRIANGLE, PULSE from constants)
        """
        self.printdebug(f"set_wave_type(channel: {channel}, wave_type: {wave_type})")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        if wave_type not in WAVE_TYPE_MAP:
            raise ValueError(f"Unsupported waveform type: {wave_type}")
        
        self.current_wave_type = wave_type
        wave_cmd = WAVE_TYPE_MAP[wave_type]
        
        # HP8116A uses FUNC command
        cmd = f"{wave_cmd}"
        self._send_command(cmd)

    def set_amplitude(self, channel: int, amplitude: float):
        """
        Set output amplitude (peak-to-peak voltage).
        
        Args:
            channel: Channel number (1 for HP8116A)
            amplitude: Amplitude in volts (0.1 V to 20 V peak)
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude: {amplitude} V)")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        if amplitude < 0.1 or amplitude > 20:
            raise ValueError(f"Amplitude {amplitude} V is out of range (0.1 V to 20 V peak)")
        
        # HP8116A uses AMP command for amplitude in volts
        cmd = f"AMP {amplitude} V"
        self._send_command(cmd)

    def set_offset(self, channel: int, offset: float):
        """
        Set DC offset voltage.
        
        Args:
            channel: Channel number (1 for HP8116A)
            offset: Offset voltage in volts (-10 V to +10 V)
        """
        self.printdebug(f"set_offset(channel: {channel}, offset: {offset} V)")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        if offset < -10 or offset > 10:
            raise ValueError(f"Offset {offset} V is out of range (-10 V to +10 V)")
        
        # HP8116A uses OFFS command
        cmd = f"OFS {offset} V"
        self._send_command(cmd)

    def set_load_impedance(self, channel: int, z: float):
        """
        Set load impedance (for informational purposes).
        
        The HP8116A has a fixed 50 ohm output impedance. This method
        stores the load impedance value for reference but doesn't actually
        change the hardware setting.
        
        Args:
            channel: Channel number (1 for HP8116A)
            z: Load impedance in ohms (use constants.HI_Z for high impedance)
        """
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance: {z})")
        
        if channel != 1:
            raise UnknownChannelError("HP8116A is a single channel device (use channel 1)")
        
        # Store for reference - HP8116A output impedance is fixed at 50 ohms
        if z == constants.HI_Z or z == float("inf"):
            self.load_impedance = float("inf")
        else:
            self.load_impedance = z
        
        # Note: HP8116A output impedance is fixed, cannot be changed via software
        self.printdebug(f"Load impedance set to {z} (stored for reference only)")


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
