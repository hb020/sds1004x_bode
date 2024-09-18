'''
Created on Nov 12, 2023

@author: donfbecker

Driver for AD9910 based AWG shield for arduino.
'''

import serial
import time
from .base_awg import BaseAWG
from .exceptions import UnknownChannelError

# Port settings
BAUD_RATE = 115000
BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
TIMEOUT = 2

# Data packet ends with CR LF (\r \n) characters
EOL = b'\x0D\x0A'

# Channels validation tuple
CHANNELS = (0, 1)
CHANNELS_ERROR = "AD9910 only has 1 channel."

# Delay between commands. AD9910 doesn't seem to need it.
SLEEP_TIME = 0.005

# Default AWG settings
DEFAULT_LOAD = 50
DEFAULT_OUTPUT_ON = False

# Output impedance of the AWG
R_IN = 50.0


class AD9910(BaseAWG):
    '''
    AD9910
    https://gra-afch.com/catalog/rf-units/dds-ad9910-arduino-shield/
    '''
    SHORT_NAME = "ad9910"

    def __init__(self, port: str = "", baud_rate: int = BAUD_RATE, timeout: int = TIMEOUT, log_debug: bool = False):        
        """baud_rate parameter is ignored."""
        super().__init__(log_debug=log_debug)
        self.printdebug("init")
        self.ser = None
        self.port = port
        self.timeout = timeout

    def _connect(self):
        self.ser = serial.Serial(self.port, BAUD_RATE, BITS, PARITY, STOP_BITS, timeout=self.timeout)

    def disconnect(self):
        self.printdebug("disconnect")
        self.ser.close()

    def _send_command(self, cmd):
        self.ser.write(cmd)
        self.ser.write(EOL)
        time.sleep(SLEEP_TIME)

    def initialize(self):
        self.printdebug("initialize")
        self._connect()
        self.output_on = DEFAULT_OUTPUT_ON
        self.enable_output(1, self.output_on)

    def get_id(self) -> str:
        return 'AD9910'

    def enable_output(self, channel: int = None, on: bool = False):
        """
        Turns the output on or off.
        """
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        self.output_on = on

        if self.output_on:
            self._send_command(b"E")
        else:
            self._send_command(b"D")

    def set_frequency(self, channel: int, freq: float):
        """
        Sets output frequency.
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        freq_str = "%.10f" % freq
        cmd = "F %s" % (freq_str)
        self._send_command(cmd.encode('utf-8'))

    def set_phase(self, channel: int, phase: float):
        """
        AD9910 does not require setting phase.
        """
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase}): ignored")

    def set_wave_type(self, channel: int, wave_type: int):
        """
        Sets the output wave type.
        """
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type}): ignored")

    def set_amplitude(self, channel: int, amplitude: float):
        """
        Sets output amplitude.
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude}): ignored")

    def set_offset(self, channel: int, offset: float):
        """
        Sets DC offset of the output.
        """
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset}): ignored")

    def set_load_impedance(self, channel: int, z: float):
        """
        Sets load impedance connected to each channel. 
        """
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z}): ignored")


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
