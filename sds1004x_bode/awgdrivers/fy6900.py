"""    
This works with newer FY6900 versions that use Hz instead of uHz.

Otherwise it is the same as the FygenAWG driver
"""

from .fy import FygenAWG

AWG_ID = "fy6900"

BAUD_RATE = 115200
TIMEOUT = 5


class Fy6900AWG(FygenAWG):
    """newer 6900 Driver API, requires Hz instead of uHz."""

    SHORT_NAME = "fy6900"

    def __init__(self, port: str = "", baud_rate: int = BAUD_RATE, timeout: int = TIMEOUT, log_debug: bool = False):
        super().__init__(port, baud_rate, timeout, log_debug)  

    def get_id(self) -> str:
        # TODO: use command "UID", from the base class
        return AWG_ID
    
    def set_frequency(self, channel: int, freq: float):
        """Sets frequency for a channel.
          freq is a floating point value in Hz.
        """
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")
        
        # for the reason of match_hz_only: see the base class
        def match_hz_only(match, got):
            if '.' in got and match == got[:got.index('.')]:
                return True
            self.printdebug('set_frequency mismatch (looking at Hz value only)')
            return False

        # at least 8 digits before the . and 6 behind.  
        # "%.6f" also works, but this is more like the latest espbode implementation to make comparisons easy
        self._retry(
            channel,
            "F",
            "%015.6f" % freq,
            "%08u" % int(freq),
            match_fn=match_hz_only)


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
