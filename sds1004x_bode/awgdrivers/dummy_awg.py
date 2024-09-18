'''
Created on Apr 24, 2018

@author: 4x1md
'''

from .base_awg import BaseAWG

AWG_ID = "Dummy AWG"


class DummyAWG(BaseAWG):
    '''
    Dummy waveform generator driver.
    '''
    SHORT_NAME = "dummy"

    def __init__(self, port: str = "", baud_rate: int = 115200, timeout: int = 5, log_debug: bool = False):
        super().__init__(log_debug=log_debug)
        self.printdebug("init")

    def disconnect(self):
        self.printdebug("disconnect")

    def initialize(self):
        self.printdebug("initialize")

    def get_id(self) -> str:
        return AWG_ID

    def enable_output(self, channel: int, on: bool):
        self.printdebug(f"enable_output(channel: {channel}, on:{on})")

    def set_frequency(self, channel: int, freq: float):
        self.printdebug(f"set_frequency(channel: {channel}, freq:{freq})")
        
    def set_phase(self, channel: int, phase: float):
        self.printdebug(f"set_phase(channel: {channel}, phase: {phase})")

    def set_wave_type(self, channel: int, wave_type: int):
        self.printdebug(f"set_wave_type(channel: {channel}, wavetype:{wave_type})")

    def set_amplitude(self, channel: int, amplitude: float):
        self.printdebug(f"set_amplitude(channel: {channel}, amplitude:{amplitude})")

    def set_offset(self, channel: int, offset: float):
        self.printdebug(f"set_offset(channel: {channel}, offset:{offset})")

    def set_load_impedance(self, channel: int, z: float):
        self.printdebug(f"set_load_impedance(channel: {channel}, impedance:{z})")
