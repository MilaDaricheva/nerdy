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

        self.mylog.info("emaUp")
        self.mylog.info(self.sm.emaUp)
        self.mylog.info("emaDown")
        self.mylog.info(self.sm.emaDown)

        self.mylog.info("positions")
        self.mylog.info(self.ib.positions())
        self.mylog.info("---------------------------")

    def specialRound(self, pr):
        # rounded = round(pr*100)/100
        minTic = 0.25
        baseP = math.floor(pr)
        leftover = pr - baseP
        nums = math.floor(leftover/minTic)
        addToBase = minTic * nums
        return round(baseP + addToBase, 2)

    def shootOneLong(self):
        self.mylog.info("Start Long1")
        lmpPrice = self.specialRound(self.arVPLong + 1)
        profPrice = self.specialRound(lmpPrice + 23)

        stopPrice = self.specialRound(lmpPrice - 28)

        bracket = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        bracket.parent.orderType = 'MKT'
        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstLong(trade)

        beStop = self.arVPLong - 3
        self.oBucket.rememberBEstop(self.specialRound(beStop))

        # remember level of entry
        self.oBucket.rememberVPLevel(self.specialRound(self.arVPLong))

    def shootTwoThreeLongs(self, t2, t3):
        lmpPrice2 = self.specialRound(self.arVPLong - t2)
        profPrice2 = self.specialRound(lmpPrice2 + 23)

        lmpPrice3 = self.specialRound(self.arVPLong - t3)
        profPrice3 = self.specialRound(lmpPrice3 + 23)

        stopPrice = self.specialRound(self.arVPLong - 28)

        self.mylog.info("Start Long2")

        bracket2 = self.ib.bracketOrder(action='BUY', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC')
        for o in bracket2:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setSecondLong(trade)

        self.mylog.info("Start Long3")

        bracket3 = self.ib.bracketOrder(action='BUY', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC')
        for o in bracket3:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setThirdLong(trade)

        # remember B/E price
        beStop = (lmpPrice2 + lmpPrice3)/2
        self.oBucket.rememberBEstop(self.specialRound(beStop))

    def manageLongs(self):

        longBigTouch = self.arVPLong > 0 and self.arVPShort == 0 and self.vpTouches.countLongT() >= 1

        cond1 = self.sm.twoStepsFromHigh and self.sm.emaUp
        cond2 = (self.sm.wobbleCond or self.sm.trendCond or self.sm.strongCond or self.sm.extremeCond) and self.sm.emaDown
        cond3 = self.sm.emaDiff > -0.7

        # flip long, close short
        if self.hasShortPos() and self.oBucket.firstShort and longBigTouch:

            if cond1 or cond2 or cond3:
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipLong = True

        noPosition = self.noPosition() and not (self.oBucket.firstLong or self.oBucket.firstShort)

        canLong = longBigTouch and noPosition

        if (canLong or self.oBucket.flipLong) and noPosition:
            self.oBucket.cancelAll()

            if cond1 or cond2:
                self.oBucket.flipLong = False
                self.oBucket.stopMoved = False
                self.oBucket.targetMoved = False

                self.printLog()

                if self.sm.emaDiff > -2:
                    # Shoot All
                    self.shootOneLong()
                    self.shootTwoThreeLongs(10, 20)
                else:
                    # Long 1
                    self.shootOneLong()
                    if self.sm.fiveStepsFromHigh:
                        # Long 2 and 3
                        self.shootTwoThreeLongs(10, 20)
                        self.oBucket.rememberTimeDump()
            elif self.sm.slowestCond or self.sm.emaDiff > 5:
                # Shoot All with diferent entries
                self.shootOneLong()
                self.shootTwoThreeLongs(3, 10)

        # Adjust orders
        if self.hasLongPos() and not self.oBucket.stopMoved:
            # see if we need to adjust bracket
            #timeInLongTrade > 620 or (emaDiff < -2 and not fiveStepsFromHigh)
            if self.oBucket.timeInPosition() > timedelta(minutes=620) or (self.sm.emaDiff < -2 and not self.sm.fiveStepsFromHigh):
                self.mylog.info("Long: Takes too long or emaDiff < -2")
                self.oBucket.adjustBraket(self.oBucket.rememberVPL + 23, self.oBucket.rememberVPL - 10)
                self.oBucket.stopMoved = True
        if self.ib.positions():
            if self.ib.positions()[0].position == 1 and self.sm.emaDiff > 2 and not self.oBucket.targetMoved:
                # make target bigger
                self.mylog.info("Long: Make target bigger")
                self.oBucket.adjustBraket(self.oBucket.rememberVPL + 75, self.oBucket.rememberVPL - 10)
                self.oBucket.targetMoved = True
                self.oBucket.stopMoved = True

    def shootOneShort(self):
        self.mylog.info("Start Short")
        lmpPrice = self.specialRound(self.arVPShort - 1)
        profPrice = self.specialRound(lmpPrice - 23)

        stopPrice = self.specialRound(lmpPrice + 28)

        bracket = self.ib.bracketOrder(action='SELL', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        bracket.parent.orderType = 'MKT'
        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstShort(trade)

        beStop = self.arVPShort + 3
        self.oBucket.rememberBEstop(self.specialRound(beStop))

        self.oBucket.rememberVPLevel(self.specialRound(self.arVPShort))

    def shootTwoThreeShorts(self):
        lmpPrice2 = self.specialRound(self.arVPShort + 10)
        profPrice2 = self.specialRound(lmpPrice2 - 23)

        lmpPrice3 = self.specialRound(self.arVPShort + 20)
        profPrice3 = self.specialRound(lmpPrice3 - 23)

        stopPrice = self.specialRound(self.arVPShort + 28)

        self.mylog.info("Start Short2")
        bracket2 = self.ib.bracketOrder(action='SELL', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC')
        for o in bracket2:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setSecondShort(trade)

        self.mylog.info("Start Short3")
        bracket3 = self.ib.bracketOrder(action='SELL', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC')
        for o in bracket3:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setThirdShort(trade)

        beStop = (lmpPrice2 + lmpPrice3)/2
        self.oBucket.rememberBEstop(self.specialRound(beStop))

    def manageShorts(self):

        shortBigTouch = self.arVPShort > 0 and self.arVPLong == 0 and self.vpTouches.countShortT() >= 1

        cond1 = self.sm.twoStepsFromLow and self.sm.emaDown and self.oBucket.timeSinceDumpOk()
        cond2 = (self.sm.wobbleCondS or self.sm.trendCondS or self.sm.strongCondS or self.sm.extremeCondS) and self.sm.emaUp and self.oBucket.timeSinceDumpOk()

        # flip short, close longs
        if self.hasLongPos() and self.oBucket.firstLong and shortBigTouch:
            if (cond1 or cond2) and (self.sm.emaDiff < -0.7 or self.sm.trendCondS):
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipShort = True
            if self.sm.emaDiff < -9:
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipShort = True

        noPosition = self.noPosition() and not (self.oBucket.firstShort or self.oBucket.firstLong)

        canShort = shortBigTouch and noPosition

        if (canShort or self.oBucket.flipShort) and noPosition:
            self.oBucket.cancelAll()

            if cond1 or cond2:
                self.oBucket.flipShort = False
                self.oBucket.stopMoved = False
                self.oBucket.targetMoved = False

                self.printLog()

                if self.sm.emaDiff < 2:
                    self.shootOneShort()
                    self.shootTwoThreeShorts()
                if self.sm.emaDiff > 2 and self.sm.sixStepsFromLow:
                    self.shootOneShort()

        if self.hasShortPos() and not self.oBucket.stopMoved:
            # see if we need to adjust bracket
            #timeInShortTrade > 620 or (emaDiff > 2 and not fiveStepsFromLow)
            if self.oBucket.timeInPosition() > timedelta(minutes=620) or (self.sm.emaDiff > 2 and not self.sm.sixStepsFromLow):
                self.mylog.info("Short: Takes too long or emaDiff > 2")
                self.oBucket.adjustBraket(self.oBucket.rememberVPL - 23, self.oBucket.rememberVPL + 10)
                self.oBucket.stopMoved = True

        if self.ib.positions():
            if self.ib.positions()[0].position == -1 and self.sm.emaDiff < -2 and not self.oBucket.targetMoved:
                # make target bigger
                self.mylog.info("Short: Make target bigger")
                self.oBucket.adjustBraket(self.oBucket.rememberVPL - 75, self.oBucket.rememberVPL + 10)
                self.oBucket.targetMoved = True
                self.oBucket.stopMoved = True

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
        self.vpTouches = vpTouches
        self.scale1Size = 1
        self.scale2Size = 1
        self.scale3Size = 1
