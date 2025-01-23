'''
Created on Jan 23, 2025

@author: hb020

This driver is based on the utg1000x driver. The only difference is that the utg900e does not support "SYSTEM:ERROR?" queries

'''

from .utg1000x import UTG1000x

TIMEOUT = 5

MYNAME = "UTG900e"


class UTG900e(UTG1000x):
    '''
    UTG900e waveform generator driver.
    '''

    SHORT_NAME = "utg900e"

    def __init__(self, port: str = "", baud_rate: int = None, timeout: int = TIMEOUT, log_debug: bool = False):
        """baud_rate parameter is ignored."""
        super().__init__(port, baud_rate, timeout, log_debug)  

    def _send_command(self, cmd):
        # local function to send a command and check for errors
        self.printdebug(f"send command \"{cmd}\"")
        self.m.write(cmd)
        return True


if __name__ == '__main__':
    print("This module shouldn't be run. Run awg_tests.py or bode.py instead.")
