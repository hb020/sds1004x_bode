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

    def __init__(self, port, baud_rate=BAUD_RATE, timeout=TIMEOUT):
        """baud_rate parameter is ignored."""
        self.port = port
        self.timeout = timeout

    def connect(self):
        self.ser = serial.Serial(self.port, BAUD_RATE, BITS, PARITY, STOP_BITS, timeout=self.timeout)

    def disconnect(self):
        self.ser.close()

    def send_command(self, cmd):
        self.ser.write(cmd)
        self.ser.write(EOL)
        time.sleep(SLEEP_TIME)

    def initialize(self):
        self.connect()
        self.r_load = DEFAULT_LOAD
        self.v_out_coeff = 1.0
        self.output_on = DEFAULT_OUTPUT_ON
        self.enable_output(1, self.output_on)

    def get_id(self) -> str:
        return 'AD9910'

    def enable_output(self, channel: int = None, on: bool = False):
        """
        Turns the output on or off.
        """
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        self.output_on = on

        if self.output_on:
            self.send_command(b"E")
        else:
            self.send_command(b"D")

    def set_frequency(self, channel: int, freq: float):
        """
        Sets output frequency.
        """
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        freq_str = "%.10f" % freq
        cmd = "F %s" % (freq_str)
        print(cmd)
        self.send_command(cmd.encode('utf-8'))

    def set_phase(self, channel: int, phase: float):
        """
        AD9910 does not require setting phase.
        """
        pass

    def set_wave_type(self, channel: int, wave_type: int):
        """
        Sets the output wave type.
        """
        pass

    def set_amplitude(self, channel: int, amplitude: float):
        """
        Sets output amplitude.
        """

        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        pass

    def set_offset(self, channel: int, offset: float):
        """
        Sets DC offset of the output.
        """
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        pass

    def set_load_impedance(self, channel: int, z: float):
        """
        Sets load impedance connected to each channel. Default value is 50 Ohms.
        """
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        self.r_load = z


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
