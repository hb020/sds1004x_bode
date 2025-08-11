'''
Created on May 15, 2018

@author: 4x1md

Update of original file on Nov. 17 2018 by Dundarave to add entries needed for FY6600 support.
'''

from awgdrivers.dummy_awg import DummyAWG
from awgdrivers.psg9080 import PSG9080
from awgdrivers.jds6600 import JDS6600
from awgdrivers.bk4075 import BK4075
from awgdrivers.fy import FygenAWG
from awgdrivers.fy6900 import Fy6900AWG
from awgdrivers.fy6600 import FY6600
from awgdrivers.ad9910 import AD9910
from awgdrivers.dg800 import RigolDG800
from awgdrivers.dg800P import RigolDG800P
from awgdrivers.utg1000x import UTG1000x
from awgdrivers.utg900e import UTG900e


class AwgFactory(object):

    def __init__(self):
        self.awgs = {}

    def add_awg(self, short_name, awg_class):
        self.awgs[short_name] = awg_class

    def get_class_by_name(self, short_name):
        return self.awgs[short_name]

    def get_names(self):
        out = []
        for a in self.awgs:
            out.append(a)
        return out


# Initialize factory
awg_factory = AwgFactory()
drivers = (
    DummyAWG,
    PSG9080,
    JDS6600,
    BK4075,
    FygenAWG,
    Fy6900AWG,
    FY6600,
    AD9910,
    RigolDG800,
    RigolDG800P,
    UTG1000x,
    UTG900e
)
for driver in drivers:
    awg_factory.add_awg(driver.SHORT_NAME, driver)
