from ib_insync import util
from ta.utils import dropna
from datetime import datetime, timedelta, time
from dateutil import tz
import pandas as pd
import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class StrategyManagement:
    def timeIsOk(self):
        # time=datetime.datetime(2021, 4, 20, 22, 0, tzinfo=datetime.timezone.utc), = 18:00 pm

        now_time = datetime.now(tz=tz.tzlocal())
        eod_time = datetime(now_time.year, now_time.month, now_time.day, 16, 0, 0, 0, tz.tzlocal())
        night_time = datetime(now_time.year, now_time.month, now_time.day, 18, 5, 0, 0, tz.tzlocal())

        # logging.info("---------")
        # logging.info(eod_time)
        # logging.info(night_time)
        # logging.info(now_time)

        if now_time < eod_time or now_time > night_time:
            return True
        else:
            return False

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
        #noLongs = bigK > 90 and bigD > 90
        return self.fK > 90 and self.fD > 90

    def noShort(self):
        #noShorts = bigK < 25 and bigD < 25
        return self.fK < 25 and self.fD < 25

    def __init__(self, bars, min_data, vp_levels):
        self.bars = dropna(util.df(bars))

        self.min_data = min_data
        self.vp_levels = vp_levels

        self.fInLong = self.min_data.getiLoc(-1)['in_long']
        self.fInShort = self.min_data.getiLoc(-1)['in_short']
        self.fK = self.min_data.getiLoc(-1)['stoch_ind_k']
        self.fD = self.min_data.getiLoc(-1)['stoch_ind_d']
