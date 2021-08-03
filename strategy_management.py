from ib_insync import util
from ta.utils import dropna
from datetime import datetime, timedelta, time
from dateutil import tz
import pandas as pd


class StrategyManagement:

    def __init__(self, bars, min_data, vp_levels, logger):
        self.mylog = logger

        self.bars = dropna(util.df(bars))

        low = self.bars.iloc[-1]['low']
        high = self.bars.iloc[-1]['high']
        step = 13

        self.min_data = min_data
        self.vp_levels = vp_levels

        highestHighBig = self.min_data.h_highs_b
        lowestLowBig = self.min_data.l_lows_b

        self.emaUp = self.min_data.getiLoc(-1)['ema_ind'] > self.min_data.getiLoc(-60)['ema_ind']
        self.emaDown = self.min_data.getiLoc(-1)['ema_ind'] < self.min_data.getiLoc(-60)['ema_ind']
        self.emaDiff = self.min_data.getiLoc(-1)['ema_ind'] - self.min_data.getiLoc(-120)['ema_ind']

        self.emaD0 = self.emaDiff < 0.7 and self.emaDiff > -0.7
        self.emaD1 = self.emaDiff < 1 and self.emaDiff > -1
        self.emaD2 = self.emaDiff < 2 and self.emaDiff > -2
        self.emaD3 = self.emaDiff < 3 and self.emaDiff > -3
        self.emaD4 = self.emaDiff < 4 and self.emaDiff > -4
        self.emaD5 = self.emaDiff < 5 and self.emaDiff > -5
        self.emaD6 = self.emaDiff < 6 and self.emaDiff > -6
        self.emaD10 = self.emaDiff < 10 and self.emaDiff > -10

        self.oneStepsFromHigh = highestHighBig - low > 0.9*step
        self.oneStepsFromLow = high - lowestLowBig > 0.9*step

        self.twoStepsFromHigh = highestHighBig - low > 1.8*step
        self.twoStepsFromLow = high - lowestLowBig > 1.8*step

        self.threeStepsFromHigh = highestHighBig - low > 2.8*step
        self.threeStepsFromLow = high - lowestLowBig > 2.8*step

        self.fourStepsFromHigh = highestHighBig - low > 3.7*step
        self.fourStepsFromLow = high - lowestLowBig > 3.7*step

        self.fiveStepsFromHigh = highestHighBig - low > 4.7*step
        self.fiveStepsFromLow = high - lowestLowBig > 4.7*step

        self.sixStepsFromHigh = highestHighBig - low > 5.7*step
        self.sixStepsFromLow = high - lowestLowBig > 5.7*step

        # Long Conditions
        self.slowestCond = self.oneStepsFromHigh and self.emaD0

        self.wobbleCond = self.twoStepsFromHigh and self.emaD3

        self.trendCond = self.threeStepsFromHigh and self.emaD6

        self.strongCond = self.fourStepsFromHigh and self.emaD10

        self.extremeCond = self.fiveStepsFromHigh and not self.emaD10

        # Short Conditions
        self.wobbleCondS = self.twoStepsFromLow and self.emaD1

        self.trendCondS = self.threeStepsFromLow and self.emaD4 and not self.emaD1

        self.strongCondS = self.fourStepsFromLow and not self.emaD4 and self.emaD5

        self.extremeCondS = self.fiveStepsFromLow and not self.emaD5

        #self.ema = self.min_data.getiLoc(-1)['ema_ind']
