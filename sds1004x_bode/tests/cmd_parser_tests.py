'''
Created on May 4, 2018

@author: 4x1md

@note: Tests the command_parser.py module.
'''

# stuff needed to get the modules from the parent directory
import sys
sys.path.insert(0, '..')

from command_parser import CommandParser
from awgdrivers.dummy_awg import DummyAWG


if __name__ == '__main__':
    with open("awg_commands_log.txt") as f:
        lines = f.readlines()

    port = "/dev/ttyUSB0"
    baud = 115200
    awg = DummyAWG(port=port, baud_rate=baud, log_debug=True)
    awg.initialize()

    parser = CommandParser(awg)

    for line in lines:
        line = line.strip()
        print(line)
        if line == "":
            continue
        parser.parse_scpi_command(line)
