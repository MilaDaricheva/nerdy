
from ib_insync import util
from ta.utils import dropna
from ta.trend import EMAIndicator
from dateutil import tz


class HRData:

    def transform_ema(self, x):
        return round(x, 2)

    def fillEma(self):
        hr_ema = EMAIndicator(close=self.bars['close'], window=120, fillna=True)
        self.bars['hr_ema'] = hr_ema.ema_indicator().apply(self.transform_ema)

    def __init__(self, bars, logger):
        self.mylog = logger
        if bars:
            self.bars = dropna(util.df(bars))
            self.fillEma()

            ptc = tz.gettz('US/Pacific')
            lastDate = bars[-1].date
            lastDate.replace(tzinfo=ptc)

            self.timeCreated = lastDate.astimezone(tz.tzutc())
        else:
            self.mylog.info("No HR bars returned.")

    def printLastN(self, n):
        self.mylog.info(self.bars.tail(n))

    def getLastN(self, n):
        return self.bars.tail(n)

    def getiLoc(self, n):
        return self.bars.iloc[n]

    def getBars(self):
        return self.bars
