'''
Created on Apr 24, 2018

@author: 4x1md
'''


class BaseAWG(object):
    '''
    Base class defining arbitrary waveform generator and its functionality.
    '''
    SHORT_NAME = "base_awg"

    def __init__(self, port: str = "", baud_rate: int = 115200, timeout: int = 5, log_debug: bool = False):
        self.log_debug = log_debug
        
    def printdebug(self, msg: str):
        if self.log_debug:
            print(f"{self.__class__.SHORT_NAME}: {msg}")
            # print(f"{self.__class__.__name__}: {msg}")

    def disconnect(self):
        raise NotImplementedError()

    def initialize(self):
        raise NotImplementedError()

    def get_id(self) -> str:
        raise NotImplementedError()

    def enable_output(self, channel: int, on: bool):
        raise NotImplementedError()

    def set_frequency(self, channel: int, freq: float):
        raise NotImplementedError()

    def set_phase(self, channel: int, phase: float):
        raise NotImplementedError()

    def set_wave_type(self, channel: int, wave_type: int):
        raise NotImplementedError()

    def set_amplitude(self, channel: int, amplitude: float):
        raise NotImplementedError()

    def set_offset(self, channel: int, offset: float):
        raise NotImplementedError()

    def set_load_impedance(self, channel: int, z: float):
        # in the hints, float means that int is also accepted
        raise NotImplementedError()
