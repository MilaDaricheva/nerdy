from ib_insync import util
from ta.utils import dropna
from ta.momentum import StochRSIIndicator
from ta.trend import EMAIndicator
import pandas as pd
from datetime import datetime, timedelta, time
from dateutil import tz


class HistData:

    def transform_val(self, x):
        return round(100*x, 2)

    def transform_ema(self, x):
        return round(x, 2)

    def fillEma(self):
        ema_ind = EMAIndicator(close=self.bars['close'], window=54, fillna=True)
        self.bars['ema_ind'] = ema_ind.ema_indicator().apply(self.transform_ema)

    def fillStoch(self, w, sl1, sl2):
        stoch_ind = StochRSIIndicator(close=self.bars['close'], window=w, smooth1=sl1, smooth2=sl2, fillna=True)
        self.bars['stoch_ind_k'] = stoch_ind.stochrsi_k().apply(self.transform_val)
        self.bars['stoch_ind_d'] = stoch_ind.stochrsi_d().apply(self.transform_val)

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

    def __init__(self, bars, logger):
        self.mylog = logger
        if bars:
            self.bars = dropna(util.df(bars))
            self.fillEma()
            #self.fillStoch(420, 90, 90)
            # self.fillStochStrategy()
            self.l_lows = self.bars['low'].tail(40).min()
            self.h_highs = self.bars['high'].tail(40).max()

            self.l_lows_b = self.bars['low'].tail(1440).min()
            self.h_highs_b = self.bars['high'].tail(1440).max()

            ptc = tz.gettz('US/Pacific')
            lastDate = bars[-1].date
            lastDate.replace(tzinfo=ptc)

            self.timeCreated = lastDate.astimezone(tz.tzutc())
        else:
            self.mylog.info("No bars returned.")

    def printLastN(self, n):
        self.mylog.info(self.bars.tail(n))

    def getLastN(self, n):
        return self.bars.tail(n)

    def getiLoc(self, n):
        return self.bars.iloc[n]

    def getBars(self):
        return self.bars
