from ib_insync import util
from ta.utils import dropna
from datetime import datetime, timedelta, time
from dateutil import tz
import pandas as pd
#import logging
#import logging.handlers as handlers

#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class StrategyManagement:

    def emaUp(self):
        return self.min_data.getiLoc(-1)['ema_ind'] > self.min_data.getiLoc(-60)['ema_ind']

    def emaDown(self):
        return self.min_data.getiLoc(-1)['ema_ind'] < self.min_data.getiLoc(-60)['ema_ind']

    def emaUpP(self):
        return self.min_data.getiLoc(-61)['ema_ind'] > self.min_data.getiLoc(-120)['ema_ind']

    def emaDownP(self):
        return self.min_data.getiLoc(-61)['ema_ind'] < self.min_data.getiLoc(-120)['ema_ind']

    # get BigD - 30min
    def bigD(self):
        return self.fD

    # get BigK - 30min
    def bigK(self):
        return self.fK

    #onlyLongs = (bigK < 20 or bigD < 25 or InLongB)
    def onlyLong(self):
        return self.fK < 20 or self.fD < 25 or self.fInLong

    #onlyShorts = (bigK > 85 or bigD > 85 or InShortB)
    def onlyShort(self):
        return self.fK > 85 or self.fD > 85 or self.fInShort

    def noLong(self):
        #bigK > 90 or bigD > 90
        return self.fK > 90 or self.fD > 90

    def noShort(self):
        #noShorts = bigK < 25 or bigD < 25
        return self.fK < 25 or self.fD < 25

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
