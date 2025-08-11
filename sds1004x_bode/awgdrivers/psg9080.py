'''
Created on August 11, 2025

@author: 4x1md, modified by nmeurer

Driver for PSG9080 AWG. This driver is very much like the JDS6600 driver.
'''

import serial
import time
from .base_awg import BaseAWG
from . import constants
from .exceptions import UnknownChannelError

# Port settings constants
BAUD_RATE = 115200
BITS = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
TIMEOUT = 5

# Data packet ends with CR LF (\r\n) characters
EOL = '\x0D\x0A'
# Channels validation tuple
CHANNELS = (0, 1, 2)
CHANNELS_ERROR = "Channel can be 1 or 2."
# delay between commands. 15msec seem to be enough, lower untested.
SLEEP_TIME = 0.015

# Output impedance of the AWG
R_IN = 50.0


class PSG9080(BaseAWG):
    '''
    PSG9080 function generator driver.
    '''
    SHORT_NAME = "psg9080"

    def __init__(self, port: str = "", baud_rate: int = BAUD_RATE, timeout: int = TIMEOUT, log_debug: bool = False):
        """baud_rate parameter is ignored."""
        super().__init__(log_debug=log_debug)
        self.printdebug("init")
        self.port = port
        self.ser = None
        self.timeout = timeout
        self.channel_on = [False, False]
        self.r_load = [50, 50]
        self.v_out_coeff = [1, 1]

    def _connect(self):
        self.ser = serial.Serial(self.port, BAUD_RATE, BITS, PARITY, STOP_BITS, timeout=self.timeout)

    def disconnect(self):
        self.printdebug("disconnect")
        self.ser.close()

    def _send_command(self, cmd):
        cmd = (cmd + EOL).encode()
        self.ser.write(cmd)
        time.sleep(SLEEP_TIME)

    def initialize(self):
        self.printdebug("initialize")
        self.channel_on = [False, False]
        self._connect()
        self.enable_output(None, False)

    def get_id(self) -> str:
        self._send_command(":r01=0.")
        ans = self.ser.read_until(".\r\n".encode("utf8"), size=None).decode("utf8")
        ans = ans.replace(":ok", "")
        return ans.strip()

    def enable_output(self, channel: int = None, on: bool = False):
        """
        Turns channels output on or off.
        The channel is defined by channel variable. If channel is None, both channels are set.

        Commands
            :w10=0,0.
            :w10=0,1.
            :w10=1,1.
        enable outputs of channels 1, 2 and of both accordingly.

        """
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        if channel is not None and channel != 0:
            self.channel_on[channel - 1] = on
        else:
            self.channel_on = [on, on]

        ch1 = "1" if self.channel_on[0] else "0"
        ch2 = "1" if self.channel_on[1] else "0"
        cmd = ":w10=%s,%s." % (ch1, ch2)
        self._send_command(cmd)

    def set_frequency(self, channel: int, freq: float):
        """
        Sets frequency on the selected channel.

        Command examples:
            :w13=25786,0.
                sets the output frequency of channel 1 to 257.86Hz.
            :w13=25786,1.
                sets the output frequency of channel 1 to 2578.6kHz.
            :w14=25786,3.
                sets the output frequency of channel 2 to 25.786mHz.
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        freq_str = "%.2f" % (freq * 10)
        freq_str = freq_str.replace(".", "")

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = ":w13=%s,1." % freq_str
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = ":w14=%s,1." % freq_str
            self._send_command(cmd)

    def set_phase(self, channel: int, phase: float):
        """
        Sends the phase setting command to the generator.
        The phase is set on channel 2 only.

        Commands
            :w21=100.
            :w21=360.
        sets the phase to 10 and 0 degrees accordingly.
        For negative values 360 degrees are considered zero point.
        """
        if phase < 0:
            phase += 360
        phase = int(round(phase * 10))
        cmd = ":w21=%s." % (phase)
        self._send_command(cmd)

    def set_wave_type(self, channel: int, wave_type: int):
        """
        Sets wave type of the selected channel.

        Commands
            :w11=0.
            :w12=0.
        set wave forms of channels 1 and 2 accordingly to sine wave.
        """
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)
        if wave_type not in constants.WAVE_TYPES:
            raise ValueError("Incorrect wave type.")

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = ":w11=%s." % wave_type
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = ":w12=%s." % wave_type
            self._send_command(cmd)

    def set_amplitude(self, channel: int, amplitude: float):
        """
        Sets amplitude of the selected channel.

        Commands
            :w15=30.
            :w16=30.
        set amplitudes of channel 1 and channel 2 accordingly to 0.03V.
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        """
        Adjust the output amplitude to obtain the requested amplitude
        on the defined load impedance.
        """
        amplitude = amplitude / self.v_out_coeff[channel - 1]

        amp_str = "%.3f" % amplitude
        amp_str = amp_str.replace(".", "")

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = ":w15=%s." % amp_str
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = ":w16=%s." % amp_str
            self._send_command(cmd)

    def set_offset(self, channel: int, offset: float):
        """
        Sets DC offset of the selected channel.

        Command examples:
            :w17=9999.
                sets the offset of channel 1 to 9.99V.
            :w17=1000.
                sets the offset of channel 1 to 0V.
            :w18=1.
                sets the offset of channel 2 to -9.99V.
        """
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        # Adjust the offset to the defined load impedance
        offset = offset / self.v_out_coeff[channel - 1]

        offset_val = 1000 + int(offset * 100)

        # Channel 1
        if channel in (0, 1) or channel is None:
            cmd = ":w17=%s." % offset_val
            self._send_command(cmd)

        # Channel 2
        if channel in (0, 2) or channel is None:
            cmd = ":w18=%s." % offset_val
            self._send_command(cmd)

    def set_load_impedance(self, channel: int, z: float):
        """
        Sets load impedance connected to each channel. Default value is 50 Ohm.
        """
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z})")
        if channel is not None and channel not in CHANNELS:
            raise UnknownChannelError(CHANNELS_ERROR)

        self.r_load[channel - 1] = z

        """
        Vout coefficient defines how the requestd amplitude must be increased
        in order to obtain the requested amplitude on the defined load.
        If the load is Hi-Z, the amplitude must not be increased.
        If the load is 50 Ohm, the amplitude has to be double of the requested
        value, because of the voltage divider between the output impedance
        and the load impedance.
        """
        if z == constants.HI_Z:
            v_out_coeff = 1
        else:
            v_out_coeff = z / (z + R_IN)
        self.v_out_coeff[channel - 1] = v_out_coeff


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
