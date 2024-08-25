'''
Created on Apr 24, 2018

@author: 4x1md
'''


class BaseAWG(object):
    '''
    Base class defining arbitrary waveform generator and its functionality.
    '''
    SHORT_NAME = "base_awg"

    def __init__(self, *args):
        pass

    def connect(self):
        raise NotImplementedError()

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
