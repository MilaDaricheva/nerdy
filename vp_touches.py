from ib_insync import MarketOrder, BracketOrder
from datetime import datetime, timedelta, time
from dateutil import tz
import numpy as np
#import logging
#import logging.handlers as handlers

#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class VpTouches:
    def addLongT(self, touch):
        self.longT.append(touch)
        if len(self.longT) > 24:
            # remove old element
            self.longT.pop(0)
        # self.mylog.info("---------------------------")
        # self.mylog.info("Long Touch")
        # self.mylog.info(self.longT)

    def countLongT(self):
        a = np.array(self.longT)
        b = a[:16]
        return np.count_nonzero(b == 1)

    def addShortT(self, touch):
        self.shortT.append(touch)
        if len(self.shortT) > 24:
            # remove old element
            self.shortT.pop(0)
        # self.mylog.info("---------------------------")
        # self.mylog.info("Short Touch")
        # self.mylog.info(self.shortT)

    def countShortT(self):
        a = np.array(self.shortT)
        b = a[:16]
        return np.count_nonzero(b == 1)

    def __init__(self, logger):
        self.mylog = logger
        self.longT = []
        self.shortT = []
