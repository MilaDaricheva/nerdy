from ib_insync import util
from ta.utils import dropna
from datetime import datetime, timedelta, time
from dateutil import tz
import pandas as pd


class StrategyManagement:

    def emaUp(self):
        return self.min_data.getiLoc(-1)['ema_ind'] > self.min_data.getiLoc(-60)['ema_ind']

    def emaDown(self):
        return self.min_data.getiLoc(-1)['ema_ind'] < self.min_data.getiLoc(-60)['ema_ind']

    def emaUpP(self):
        return self.min_data.getiLoc(-61)['ema_ind'] > self.min_data.getiLoc(-120)['ema_ind']

    def emaDownP(self):
        return self.min_data.getiLoc(-61)['ema_ind'] < self.min_data.getiLoc(-120)['ema_ind']

    def emaDiff(self):
        return self.min_data.getiLoc(-1)['ema_ind'] - self.min_data.getiLoc(-120)['ema_ind']

    def emaNearLong(self, aroundVPLevel):
        #emaNearLong = ema30 > aroundVPLevel and ema30 < aroundVPLevel + 2
        return self.min_data.getiLoc(-1)['ema_ind'] > aroundVPLevel and self.min_data.getiLoc(-1)['ema_ind'] < aroundVPLevel + 2

    def emaNearShort(self, aroundVPLevel):
        #ema30 < aroundVPLevelToShort and ema30 > aroundVPLevelToShort - 2
        return self.min_data.getiLoc(-1)['ema_ind'] < aroundVPLevel and self.min_data.getiLoc(-1)['ema_ind'] > aroundVPLevel - 2

    # get BigD - 30min

    def bigD(self):
        return self.fD

    # get BigK - 30min
    def bigK(self):
        return self.fK

    # onlyLongs = (emaUp or InLongB)
    def onlyLong(self):
        return self.emaUp or self.fInLong

    # onlyShorts = (emaDown or InShortB)
    def onlyShort(self):
        return self.emaDown or self.fInShort

    def noLong(self):
        # noLongs = bigK > 50 or bigD > 50
        return self.fK > 50 or self.fD > 50

    def noShort(self):
        # noShorts = bigK < 50 or bigD < 50
        return self.fK < 50 or self.fD < 50

    def tooHigh(self):
        # tooHigh = bigK > 80 or bigD > 80
        return self.fK > 80 or self.fD > 80

    def tooLow(self):
        # tooLow = bigK < 21 or bigD < 21
        return self.fK < 21 or self.fD < 21

    def __init__(self, bars, min_data, vp_levels, logger):
        self.mylog = logger

        self.bars = dropna(util.df(bars))

        self.min_data = min_data
        self.vp_levels = vp_levels

        self.fInLong = self.min_data.getiLoc(-1)['in_long']
        self.fInShort = self.min_data.getiLoc(-1)['in_short']
        self.fK = self.min_data.getiLoc(-1)['stoch_ind_k']
        self.fD = self.min_data.getiLoc(-1)['stoch_ind_d']

        self.ema = self.min_data.getiLoc(-1)['ema_ind']
