from ib_insync import MarketOrder, BracketOrder
from datetime import datetime, timedelta, time
from dateutil import tz
from orders_bucket import OrdersBucket
import math


class OrderManagement:
    def noPosition(self):
        return not self.ib.positions()

    def hasLongPos(self):
        if self.noPosition():
            return False
        else:
            return self.ib.positions()[0].position > 0

    def hasShortPos(self):
        if self.noPosition():
            return False
        else:
            return self.ib.positions()[0].position < 0

    def printLog(self):
        self.mylog.info("---------------------------")
        self.mylog.info("prev fast ema")
        self.mylog.info(self.sm.min_data.getiLoc(-3)['ema_ind'])

        self.mylog.info("slower ema")
        self.mylog.info(self.sm.hr_data.getiLoc(-1)['hr_ema'])

        self.mylog.info("fast ema")
        self.mylog.info(self.sm.min_data.getiLoc(-1)['ema_ind'])

        self.mylog.info("---------------------------")

    def specialRound(self, pr):
        # rounded = round(pr*100)/100
        minTic = 0.25
        baseP = math.floor(pr)
        leftover = pr - baseP
        nums = math.floor(leftover/minTic)
        addToBase = minTic * nums
        return round(baseP + addToBase, 2)

    def shootOneLong(self, t1, prof1, mkt):
        self.mylog.info("Start Long1")
        lmpPrice = self.specialRound(t1)
        profPrice = self.specialRound(t1 + prof1)
        stopPrice = self.specialRound(t1 - 60)

        bracket = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        if mkt:
            bracket.parent.orderType = 'MKT'

        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstLong(trade)
            self.mylog.info(o)

        # remember level of entry
        self.oBucket.rememberVPLevel(self.specialRound(self.fastEma))

    def shootOneShort(self, t1, prof1, mkt):
        self.mylog.info("Start Short1")
        lmpPrice = self.specialRound(t1)
        profPrice = self.specialRound(t1 - prof1)
        stopPrice = self.specialRound(t1 + 60)

        bracket = self.ib.bracketOrder(action='SELL', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        if mkt:
            bracket.parent.orderType = 'MKT'

        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstShort(trade)
            self.mylog.info(o)

        # remember level of entry
        self.oBucket.rememberVPLevel(self.specialRound(self.fastEma))

    def manageLongs(self):
        noPosition = self.noPosition() and not (self.oBucket.firstLong or self.oBucket.firstShort)

        if self.sm.crossUp and self.hasShortPos():
            self.mylog.info("flip long close short")
            self.oBucket.flipLong = True
            self.oBucket.closeAll()

        #canLong = self.sm.crossUp and noPosition

        if (self.sm.crossUp or self.oBucket.flipLong) and noPosition:
            self.mylog.info("Open long")
            self.printLog()
            self.oBucket.flipLong = False
            # self.oBucket.cancelAll()
            # target, profit, markt or not
            self.shootOneLong(self.closingPr, 200, True)
            self.shootOneLong((self.closingPr + self.fastEma)*0.5, 15, False)

        # check for no fill
        # if self.oBucket.firstLong and self.noPosition() and self.oBucket.timeInPosition() > timedelta(minutes=180):
        #    self.oBucket.cancelAll()

    def manageShorts(self):

        noPosition = self.noPosition() and not (self.oBucket.firstLong or self.oBucket.firstShort)

        if self.sm.crossDown and self.hasLongPos():
            self.mylog.info("flip short close long")
            self.oBucket.flipShort = True
            self.oBucket.closeAll()

        #canShort = self.sm.crossDown and noPosition

        if (self.sm.crossDown or self.oBucket.flipShort) and noPosition:
            self.mylog.info("Open short")
            self.printLog()
            self.oBucket.flipShort = False
            # self.oBucket.cancelAll()
            # target, profit, markt or not
            self.shootOneShort(self.closingPr, 200, True)
            self.shootOneShort(self.fastEma, 15, False)

        # check for no fill
        # if self.oBucket.firstShort and self.noPosition() and self.oBucket.timeInPosition() > timedelta(minutes=180):
        #    self.oBucket.cancelAll()

    def goDoBusiness(self):
        if self.arVPLong > 0 and self.arVPShort == 0:
            self.vpTouches.addLongT(1)
            # self.printLog()
        else:
            self.vpTouches.addLongT(0)

        if self.arVPShort > 0 and self.arVPLong == 0:
            self.vpTouches.addShortT(1)
            # self.printLog()
        else:
            self.vpTouches.addShortT(0)

        self.manageLongs()
        self.manageShorts()

    def __init__(self, ib, contract, sm, oBucket, rtd, vpTouches, logger):
        self.mylog = logger
        self.ib = ib
        self.contract = contract
        self.sm = sm
        self.oBucket = oBucket
        self.rtd = rtd
        self.arVPLong = self.rtd.aroundVPLong()
        self.arVPShort = self.rtd.aroundVPShort()
        self.fastEma = self.sm.min_data.getiLoc(-1)['ema_ind']
        self.closingPr = self.rtd.bars.iloc[-1]['close']
        self.vpTouches = vpTouches
        self.scale1Size = 1
        self.scale2Size = 1
        self.scale3Size = 1
