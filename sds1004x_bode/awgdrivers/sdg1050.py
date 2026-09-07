'''
Siglent SDG1050 waveform generator driver.
Based on UTG1000x driver structure.
'''

from .base_awg import BaseAWG
from . import constants
import pyvisa as visa
from .exceptions import UnknownChannelError

TIMEOUT = 5

CHANNELS = (0, 1, 2)  # SDG1050 has 2 channels. Channel 0 will be used to refer to both channels together.
MYNAME = "SDG1050"
CHANNELS_ERROR = f"{MYNAME} has only 2 channels."

# Map internal wave type constants to SDG1050 commands
# Only use constants that definitely exist
WAVEFORM_COMMANDS = {
    constants.SINE: "SINE",
    constants.SQUARE: "SQUARE",
    constants.PULSE: "PULSE",
    constants.TRIANGLE: "RAMP",
    # constants.NOISE and constants.DC might not exist, so omit them for now
}

# Default AWG settings
DEFAULT_LOAD = 50
DEFAULT_OUTPUT_ON = False


class SDG1050(BaseAWG):
    '''
    Siglent SDG1050 waveform generator driver.
    '''

    SHORT_NAME = "sdg1050"

    def __init__(self, port: str = "", baud_rate: int = None, 
                 timeout: int = TIMEOUT, log_debug: bool = False, 
                 force_pyvisa_py: bool = False):
        """Initialize the SDG1050 driver.
        
        Args:
            port: VISA resource string (e.g., "ASRL/dev/cu.usbserial-57670683761::INSTR")
            baud_rate: Ignored for USB devices
            timeout: Timeout in seconds
            log_debug: Enable debug logging
        """
        super().__init__(log_debug=log_debug, force_pyvisa_py=force_pyvisa_py)
        self.printdebug("init")
        self.port = port
        self.rm = None
        self.inst = None
        self.timeout = timeout
        self.channel_on = [False, False]  # Dual channel
        self.r_load = [DEFAULT_LOAD, DEFAULT_LOAD]
        
        # For voltage adjustment based on load (SDG series handles this internally)
        self.v_out_coeff = [1.0, 1.0]

    def _send_command(self, cmd: str) -> bool:
        """Send a command to the SDG1050.
        
        Args:
            cmd: The SCPI command to send
            
        Returns:
            True if command succeeded, False otherwise
        """
        self.printdebug(f"send command \"{cmd}\"")
        try:
            self.inst.write(cmd)
            return True
        except Exception as e:
            print(f"ERR: command \"{cmd}\" failed: {e}")
            return False

    def _query(self, cmd: str) -> str:
        """Send a query to the SDG1050 and return the response.
        
        Args:
            cmd: The SCPI query to send
            
        Returns:
            Response string
        """
        self.printdebug(f"query \"{cmd}\"")
        try:
            response = self.inst.query(cmd)
            return response.strip()
        except Exception as e:
            print(f"ERR: query \"{cmd}\" failed: {e}")
            return ""

    def _connect(self):
        """Establish connection to the SDG1050."""
        self.printdebug("connecting")
        self.rm = visa.ResourceManager("@py" if self.force_pyvisa_py else "")
        
        # Handle both full VISA strings and raw serial ports
        if self.port.startswith('ASRL') or '::' in self.port:
            # Full VISA resource string
            self.inst = self.rm.open_resource(self.port)
        else:
            # Assume it's just a serial port path
            self.inst = self.rm.open_resource(f"ASRL{self.port}::INSTR")
            
        self.inst.timeout = self.timeout * 1000
        
        # Set encoding to handle any special characters
        self.inst.encoding = 'latin-1'
        
        # Set termination characters as expected by SDG series
        self.inst.write_termination = '\n'
        self.inst.read_termination = '\n'

    def disconnect(self):
        """Disconnect from the SDG1050."""
        self.printdebug("disconnect")
        if self.inst is not None:
            # Turn off output before disconnecting
            try:
                self.enable_output(0, False)
            except:
                pass
            self.inst.close()
            self.inst = None
        if self.rm is not None:
            self.rm.close()
            self.rm = None

    def initialize(self):
        """Initialize the SDG1050."""
        self.printdebug("initialize")
        self._connect()
        # Clear any errors and reset to known state
        self._send_command("*CLS")
        
        # Don't send *RST as it might reset too many settings
        # Instead, ensure sine wave output
        self.set_wave_type(1, constants.SINE)

    def get_id(self) -> str:
        """Get instrument identification."""
        return self._query("*IDN?").strip()

    def enable_output(self, channel: int, on: bool):
        """Enable or disable the output.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            on: True to turn on, False to turn off
        """
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.enable_output(1, on)
            self.enable_output(2, on)
        else:
            self.channel_on[channel - 1] = on
            state = "ON" if on else "OFF"
            self._send_command(f"C{channel}:OUTP {state}")

    def set_frequency(self, channel: int, freq: float):
        """Set the output frequency.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            freq: Frequency in Hz
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_frequency(1, freq)
            self.set_frequency(2, freq)
        else:
            self._send_command(f"C{channel}:BSWV FRQ,{freq:.10f}")

    def set_phase(self, channel: int, phase: float):
        """Set the output phase.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            phase: Phase in degrees
        """
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase})")
        
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_phase(1, phase)
            self.set_phase(2, phase)
        else:
            # Normalize phase to 0-360 range
            phase = phase % 360
            self._send_command(f"C{channel}:BSWV PHSE,{phase}")

    def set_wave_type(self, channel: int, wave_type: int):
        """Set the waveform type.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            wave_type: One of the constants from constants.py
        """
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type})")

        if wave_type not in WAVEFORM_COMMANDS:
            # If waveform type not in our map, default to SINE
            self.printdebug(f"Wave type {wave_type} not supported, defaulting to SINE")
            wave_name = "SINE"
        else:
            wave_name = WAVEFORM_COMMANDS[wave_type]

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_wave_type(1, wave_type)
            self.set_wave_type(2, wave_type)
        else:
            self._send_command(f"C{channel}:BSWV WVTP,{wave_name}")

    def set_amplitude(self, channel: int, amplitude: float):
        """Set the output amplitude.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            amplitude: Amplitude in Vpp
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_amplitude(1, amplitude)
            self.set_amplitude(2, amplitude)
        else:
            # SDG series expects amplitude in Vpp
            self._send_command(f"C{channel}:BSWV AMP,{amplitude:.3f}")

    def set_offset(self, channel: int, offset: float):
        """Set the DC offset.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            offset: DC offset in volts
        """
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset})")
        
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_offset(1, offset)
            self.set_offset(2, offset)
        else:
            self._send_command(f"C{channel}:BSWV OFST,{offset:.3f}")

    def set_load_impedance(self, channel: int, z: float):
        """Set the output load impedance.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            z: Load impedance in ohms, or constants.HI_Z for high impedance
        """
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z})")

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_load_impedance(1, z)
            self.set_load_impedance(2, z)
        else:
            if z == constants.HI_Z or z > 10000:
                # High impedance mode
                self._send_command(f"C{channel}:OUTP LOAD,HZ")
                self.v_out_coeff[channel - 1] = 1.0
            else:
                # Fixed load in ohms
                self._send_command(f"C{channel}:OUTP LOAD,{int(z)}")
                self.v_out_coeff[channel - 1] = 1.0  # SDG handles compensation internally

    # Additional SDG1050-specific methods that might be useful

    def set_sync(self, channel: int, on: bool):
        """Enable or disable sync output.
        
        Args:
            channel: Channel number (1, 2, or 0 for both)
            on: True to enable sync, False to disable
        """
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is None or channel == 0:
            self.set_sync(1, on)
            self.set_sync(2, on)
        else:
            state = "ON" if on else "OFF"
            self._send_command(f"C{channel}:OUTP SYNC,{state}")

    def get_status(self) -> str:
        """Get instrument status."""
        return self._query("SYST:STAT?")

    def clear_status(self):
        """Clear status registers."""
        self._send_command("*CLS")


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
