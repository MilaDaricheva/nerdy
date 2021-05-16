from ib_insync import util
from ta.utils import dropna
from ta.momentum import StochRSIIndicator
from ta.trend import EMAIndicator
import pandas as pd
from datetime import datetime, timedelta, time
from dateutil import tz
import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class HistData:

    def transform_stoch_val(self, x):
        return round(100*x, 2)

    def fillStoch(self, w, sl1, sl2):
        stoch_ind = StochRSIIndicator(close=self.bars['close'], window=w, smooth1=sl1, smooth2=sl2, fillna=True)
        self.bars['stoch_ind_k'] = stoch_ind.stochrsi_k().apply(self.transform_stoch_val)
        self.bars['stoch_ind_d'] = stoch_ind.stochrsi_d().apply(self.transform_stoch_val)

    def fillStochStrategy(self):
        stoch_sensitivity = 1
        in_long = []
        in_short = []
        enter_long = []
        enter_short = []
        k = self.bars['stoch_ind_k']
        d = self.bars['stoch_ind_d']

        for i in range(len(k)):
            in_long.append(False)
            in_short.append(False)
            enter_long.append(False)
            enter_short.append(False)
            if i > 1:
                enter_long[i] = k[i] > d[i] + stoch_sensitivity and k[i - 1] <= d[i-1] + stoch_sensitivity and not in_long[i-1]
                enter_short[i] = k[i] < d[i] - stoch_sensitivity and k[i - 1] >= d[i-1] - stoch_sensitivity and not in_short[i-1]
                in_long[i] = enter_long[i] or in_long[i - 1] and not enter_short[i]
                in_short[i] = enter_short[i] or in_short[i - 1] and not enter_long[i]

        stoch_df = pd.DataFrame(list(zip(in_long, in_short, enter_long, enter_short)), columns=['in_long', 'in_short', 'enter_long', 'enter_short'])

        result = pd.concat([self.bars, stoch_df], axis=1, join="inner")
        self.bars = result

    def __init__(self, bars):

        self.bars = dropna(util.df(bars))
        self.fillStoch(420, 90, 90)
        self.fillStochStrategy()
        self.l_lows = self.bars['low'].tail(60).min()
        self.h_highs = self.bars['high'].tail(60).max()

        ptc = tz.gettz('US/Pacific')
        lastDate = bars[-1].date
        lastDate.replace(tzinfo=ptc)

        self.timeCreated = lastDate.astimezone(tz.tzutc())
        logging.info(bars[-1])

    def printLastN(self, n):
        logging.info(self.bars.tail(n))

    def getLastN(self, n):
        return self.bars.tail(n)

    def getiLoc(self, n):
        return self.bars.iloc[n]

    def getBars(self):
        return self.bars
