"""
Minimalist driver for FYXXXX signal generators.
For a full-featured implementation of all AWG features, see:
    https://github.com/mattwach/fygen
    
This works with FY2300, FY6600, FY6800, FY6900 and probably more

The main difference is that it uses read/retries instead of a fixed
timeout.  This speeds up commands.  In measurement, a 50 point bode
plot sped up from 112 seconds to 68 seconds.

I named the driver fy.py to keep the fy6600.py file intact and to
make it clearer that the driver is not limited to the fy6600.  We
could also set things up differently, if you would prefer.
"""

import serial
import time

from .exceptions import UnknownChannelError
from .base_awg import BaseAWG

AWG_ID = "fy"
AWG_OUTPUT_IMPEDANCE = 50.0
MAX_READ_SIZE = 256
RETRY_COUNT = 2
MAX_RETRIES = 5

BAUD_RATE = 115200
TIMEOUT = 5


class FygenAWG(BaseAWG):
    """Driver API."""

    SHORT_NAME = "fy"

    def __init__(self, port: str = "", baud_rate: int = BAUD_RATE, timeout: int = TIMEOUT, log_debug: bool = False):
        """baud_rate parameter is ignored."""
        super().__init__(log_debug=log_debug)
        self.printdebug("init")
        self.fy = None
        self.ser = None
        self.port = port
        self.timeout = timeout
        # None -> Hi-Z
        self.load_impedance = {
            1: None,
            2: None,
        }

    def _connect(self):
        if self.ser:
            return

        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            rtscts=False,
            dsrdtr=False,
            xonxoff=False,
            timeout=self.timeout)

        self.printdebug(f"Connected to {self.port}")
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()

    def disconnect(self):
        self.printdebug("disconnect")
        if self.ser:
            self.printdebug("Disconnected from {self.port}")
            self.ser.close()
            self.ser = None

    def initialize(self):
        self._connect()
        self.enable_output(0, False)

    def get_id(self) -> str:
        # TODO: use command "UID"
        return AWG_ID

    def enable_output(self, channel: int, on: bool):
        """Turns a channel on (True) or off (False)."""
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")
        self._retry(
            channel,
            "N",
            "1" if on else "0",
            "255" if on else "0") 

    def set_frequency(self, channel: int, freq: float):
        """Sets frequency for a channel.
          freq is a floating point value in Hz.
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")
        uhz = int(freq * 1000000.0)

        # AWG Bug: With the FY2300 and some values of frequency (for example
        # 454.07 Hz) a bug occurs where the UI of the generator shows the
        # correct value on the UI but the "RMF" command returns an incorrect
        # fractional hertz value (454.004464 Hz for the example above).
        # The work-around is to just match the Hz part of the return
        # value.
        def match_hz_only(match, got):
            if '.' in got and match == got[:got.index('.')]:
                return True
            self.printdebug('set_frequency mismatch (looking at Hz value only)')
            return False

        self._retry(
            channel,
            "F",
            "%014u" % uhz,
            "%08u" % int(freq),
            match_fn=match_hz_only)

    def set_phase(self, channel: int, phase: float):
        """Sets the phase of a channel in degrees."""
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase}), but forced on channel 2")
        channel = 2  # This parameter is ignored, always set phase on channel 2 (not sure why)
        self._retry(
            channel,
            "P",
            "%.3f" % phase,
            "%u" % (phase * 1000))

    def set_wave_type(self, channel: int, wave_type: int):
        """Sets a channel to a sin wave."""
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type}), but forcing sine wave")
        self._retry(channel, "W", "0", "0")

    def set_amplitude(self, channel: int, amplitude: float):
        """Sets a channel amplitude in volts.
          Load impedeance for the channel is taken into account
          when calculating the amplitude.  For example, if the load
          impedance is 50 ohms and amp=50 ohms, the actual voltage
          set is 1 * (50 + 50) / 50 = 2V.
        """
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude})")
        volts = round(self._apply_load_impedance(channel, amplitude), 4)
        self._retry(
            channel,
            "A",
            "%.4f" % volts,
            "%u" % (volts * 10000))

    def set_offset(self, channel: int, offset: float):
        """Sets the voltage offset for a channel.
          offset is a floating point number.
        """
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset})")
        # Factor in load impedance.
        offset = self._apply_load_impedance(channel, offset)

        # AWG Bug: The FY2300 returns negative offsets as
        # an unsigned integer.  Thus math is needed to predict
        # the returned value correctly
        offset_unsigned = int(round(offset, 3) * 1000.0)
        if offset_unsigned < 0:
            offset_unsigned = 0x100000000 + offset_unsigned
        self._retry(
            channel,
            "O",
            "%.3f" % offset,
            "%u" % offset_unsigned)

    def set_load_impedance(self, channel: int, z: float):
        """Sets the load impedance for a channel."""
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z})")
        maxz = 10000000.0
        if z > maxz:
            z = None  # Hi-z
        self.load_impedance[channel] = z

    def _apply_load_impedance(self, channel: int, volts):
        if channel not in self.load_impedance:
            raise UnknownChannelError("Unknown channel: %s" % channel)
        if not self.load_impedance[channel]:
            return volts  # Hi-Z
        loadz = self.load_impedance[channel]
        return volts * (AWG_OUTPUT_IMPEDANCE + loadz) / loadz

    def _recv(self, command):
        """Waits for device."""
        response = self.ser.read_until(size=MAX_READ_SIZE).decode("utf8")
        self.printdebug(f"{command.strip()} -> {response.strip()}")
        return response

    def _send(self, command, retry_count=MAX_RETRIES):
        """Sends a low-level command. Returns the response."""
        self.printdebug(f"send (attempt {MAX_RETRIES + 1 - retry_count}/{MAX_RETRIES}) -> {command}")

        data = command + "\n"
        data = data.encode()
        self.ser.reset_output_buffer()
        self.ser.reset_input_buffer()
        self.ser.write(data)
        self.ser.flush()

        response = self._recv(command)

        if not response and retry_count > 1:
            # sometime the siggen answers queries with nothing.  Wait a bit,
            # then try again
            time.sleep(0.1)
            return self._send(command, retry_count - 1)

        return response.strip()

    def _retry(self, channel: int, command, value, match, match_fn=None):
        """Retries the command until match is satisfied."""
        if channel is None or channel == 0:
            self._retry(1, command, value, match)
            self._retry(2, command, value, match)
            return
        elif channel == 1:
            channel = "M"
        elif channel == 2:
            channel = "F"
        else:
            raise UnknownChannelError("Channel shoud be 1 or 2")

        if not match_fn:
            # usually we want ==
            def match_fn(match, got):
                return match == got

        if match_fn(match, self._send("R" + channel + command)):
            self.printdebug(f"already set {match}")
            return

        for _ in range(RETRY_COUNT):
            self._send("W" + channel + command + value)
            if match_fn(match, self._send("R" + channel + command)):
                self.printdebug(f"matched {match}")
                return
            self.printdebug(f"mismatched {match}")

        # Print a warning.  This is not an error because the AWG read bugs
        # worked-around in this module could vary by AWG model number or
        # firmware revision number.
        print(f"Warning: {'W' + channel + command + value} did not produce an expected response after {RETRY_COUNT} retries")
        

if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
