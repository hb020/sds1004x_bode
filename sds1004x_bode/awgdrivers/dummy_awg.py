'''
Created on Apr 24, 2018

@author: 4x1md
'''

from .base_awg import BaseAWG

AWG_ID = "Dummy AWG"

DEBUG_OUT = True


class DummyAWG(BaseAWG):
    '''
    Dummy waveform generator driver.
    '''

    SHORT_NAME = "dummy"

    def __init__(self, *args):
        if DEBUG_OUT:
            print("Dummy: init")

    def connect(self):
        if DEBUG_OUT:
            print("Dummy: connect")

    def disconnect(self):
        if DEBUG_OUT:
            print("Dummy: disconnect")

    def initialize(self):
        if DEBUG_OUT:
            print("Dummy: initialize")

    def get_id(self):
        return AWG_ID

    def enable_output(self, channel, on):
        if DEBUG_OUT:
            print(f"Dummy: enable_output(channel: {channel}, on:{on})")

    def set_frequency(self, channel, freq):
        if DEBUG_OUT:
            print(f"Dummy: set_frequency(channel: {channel}, freq:{freq})")
        
    def set_phase(self, channel, phase):
        if DEBUG_OUT:
            print(f"Dummy: set_phase(phase: {phase})")

    def set_wave_type(self, channel, wvtp):
        if DEBUG_OUT:
            print(f"Dummy: set_wave_type(channel: {channel}, wavetype:{wvtp})")

    def set_amplitude(self, channel, amp):
        if DEBUG_OUT:
            print(f"Dummy: set_amplitude(channel: {channel}, amplitude:{amp})")

    def set_offset(self, channel, offset):
        if DEBUG_OUT:
            print(f"Dummy: set_offset(channel: {channel}, offset:{offset})")

    def set_load_impedance(self, channel, z):
        if DEBUG_OUT:
            print(f"Dummy: set_load_impedance(channel: {channel}, impedance:{z})")
