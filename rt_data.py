from ib_insync import util
from ta.utils import dropna
import pandas as pd
#import logging
#import logging.handlers as handlers

#logging.basicConfig(filename='RT_data.log', encoding='utf-8', level=logging.INFO)


class RealTimeData:

    def aroundVPLong(self):
        aroundVPLevel = 0
        vp_size = len(self.vp_levels)
        vp = self.vp_levels
        lowest_low = self.min_data.l_lows
        low = self.bars.iloc[-1]['low']
        high = self.bars.iloc[-1]['high']
        close = self.bars.iloc[-1]['close']
        for i in range(vp_size):
            if (low <= vp[i] + 3) and (close > vp[i]) and (high - low < 5) and (lowest_low > vp[i] - 1):
                aroundVPLevel = vp[i]
        return aroundVPLevel

    def aroundVPShort(self):
        aroundVPLevel = 0
        vp_size = len(self.vp_levels)
        vp = self.vp_levels
        highest_high = self.min_data.h_highs
        low = self.bars.iloc[-1]['low']
        high = self.bars.iloc[-1]['high']
        for i in range(vp_size):
            if (high < vp[i] + 1) and (high >= vp[i] - 3) and (high - low < 5) and (highest_high < vp[i] + 1):
                aroundVPLevel = vp[i]
        return aroundVPLevel

    def __init__(self, bars, min_data, hr_data, vp_levels, logger):
        self.mylog = logger
        # 12 bars per min
        self.bars = dropna(util.df(bars))
        self.min_data = min_data
        self.hr_data = hr_data
        self.vp_levels = vp_levels

    def printLastN(self, n):
        self.mylog.info(self.bars.tail(n))

    def getiLoc(self, n):
        return self.bars.iloc[n]

    def getBars(self):
        return self.bars
