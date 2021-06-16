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
        self.mylog.info(self.sm.emaUp())
        self.mylog.info("emaDown")
        self.mylog.info(self.sm.emaDown())

        self.mylog.info("onlyLong")
        self.mylog.info(self.sm.onlyLong())
        self.mylog.info("onlyShort")
        self.mylog.info(self.sm.onlyShort())
        self.mylog.info("noLong")
        self.mylog.info(self.sm.noLong())
        self.mylog.info("noShort")
        self.mylog.info(self.sm.noShort())

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
        profPrice = self.specialRound(lmpPrice + 30)

        stopPrice = self.specialRound(lmpPrice - 23)

        if self.sm.onlyShort():
            stopPrice = self.specialRound(lmpPrice - 15)

        bracket = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        bracket.parent.orderType = 'MKT'
        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstLong(trade)

        beStop = self.arVPLong - 3
        self.oBucket.rememberBEstop(self.specialRound(beStop))

        # remember level of entry
        self.oBucket.rememberVPLevel(self.specialRound(self.arVPLong))

    def shootTwoThreeLongs(self):
        lmpPrice2 = self.specialRound(self.arVPLong - 4)
        profPrice2 = self.specialRound(lmpPrice2 + 10)

        stopPrice = self.specialRound(self.arVPLong - 22)

        lmpPrice3 = self.specialRound(self.arVPLong - 10)
        profPrice3 = self.specialRound(lmpPrice3 + 20)

        if self.sm.onlyShort():
            profPrice2 = self.specialRound(lmpPrice2 + 10)
            profPrice3 = self.specialRound(lmpPrice3 + 10)
            stopPrice = self.specialRound(self.arVPLong - 15)

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

        longBigTouch = self.arVPLong > 0 and self.arVPShort == 0 and self.vpTouches.countLongT() > 1

        # flip long, close short
        if self.hasShortPos() and self.oBucket.firstShort and longBigTouch:
            #  if ((onlyLongs and not noLongs and InLongB) or noShorts) and not (emaNearLong and InShortB)
            if ((self.sm.onlyLong() and not self.sm.noLong() and self.sm.fInLong) or self.sm.noShort()) and not (self.sm.emaNearLong(self.arVPLong) and self.sm.fInShort):
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipLong = True

        noPosition = self.noPosition() and not self.oBucket.firstLong

        canLong = longBigTouch and noPosition

        if (canLong or self.oBucket.flipLong) and noPosition:
            # if emaDiff > -0.55 and emaDiff < 0.55 and noShorts and not (emaNearLong and InShortB)
            wobbleZone = self.sm.emaDiff() > -0.55 and self.sm.emaDiff() < 0.55

            if wobbleZone and self.sm.noShort() and not (self.sm.emaNearLong(self.arVPLong) and self.sm.fInShort):
                self.oBucket.flipLong = False
                self.oBucket.stopMoved = False
                self.printLog()

                # Long 1
                self.shootOneLong()
                # Long 2 and 3
                self.shootTwoThreeLongs()

                # else if ((onlyLongs and not noLongs and InLongB) or tooLow) and not (emaNearLong and InShortB)
            elif ((self.sm.onlyLong() and not self.sm.noLong() and self.sm.fInLong) or self.sm.tooLow()) and not (self.sm.emaNearLong(self.arVPLong) and self.sm.fInShort):
                self.oBucket.flipLong = False
                self.oBucket.stopMoved = False
                self.printLog()

                # Long 1
                self.shootOneLong()

                if not self.sm.onlyShort():
                    # Long 2 and 3
                    self.shootTwoThreeLongs()

    def shootOneShort(self):
        self.mylog.info("Start Short")
        lmpPrice = self.specialRound(self.arVPShort - 1)
        profPrice = self.specialRound(lmpPrice - 30)

        stopPrice = self.specialRound(lmpPrice + 23)

        if self.sm.onlyLong():
            profPrice = self.specialRound(lmpPrice - 10)
            stopPrice = self.specialRound(lmpPrice + 15)

        bracket = self.ib.bracketOrder(action='SELL', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        bracket.parent.orderType = 'MKT'
        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstShort(trade)

        beStop = self.arVPShort + 3
        self.oBucket.rememberBEstop(self.specialRound(beStop))

        self.oBucket.rememberVPLevel(self.specialRound(self.arVPShort))

    def shootTwoThreeShorts(self):

        lmpPrice2 = self.specialRound(self.arVPShort + 3)
        profPrice2 = self.specialRound(lmpPrice2 - 10)

        stopPrice = self.specialRound(self.arVPShort + 22)

        lmpPrice3 = self.specialRound(self.arVPShort + 10)
        profPrice3 = self.specialRound(lmpPrice3 - 20)

        if self.sm.onlyLong():
            profPrice2 = self.specialRound(lmpPrice2 - 4)
            profPrice3 = self.specialRound(lmpPrice3 - 10)
            stopPrice = self.specialRound(self.arVPShort + 18)

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

        shortBigTouch = self.arVPShort > 0 and self.arVPLong == 0 and self.vpTouches.countShortT() > 1

        # flip short, close longs
        lowOfBar = self.rtd.getiLoc(-1).low
        wobbleZone = self.sm.emaDiff() > -0.55 and self.sm.emaDiff() < 0.55

        if self.hasLongPos() and self.oBucket.firstLong and shortBigTouch:
            # if emaDiff > -0.55 and emaDiff < 0.55 and noLongs
            if wobbleZone and self.sm.noLong():
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipShort = True
            # else if (onlyShorts and not noShorts and not onlyLongs) or (InShortB and emaNearShort)
            elif (self.sm.onlyShort() and not self.sm.noShort() and not self.sm.onlyLong()) or (self.sm.fInShort and self.sm.emaNearShort(self.arVPShort)):
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipShort = True

        noPosition = self.noPosition() and not self.oBucket.firstShort

        canShort = shortBigTouch and noPosition

        if (canShort or self.oBucket.flipShort) and noPosition:
            # if emaDiff > -0.55 and emaDiff < 0.55 and noLongs
            if wobbleZone and self.sm.noLong():
                self.oBucket.flipShort = False
                self.oBucket.stopMoved = False

                self.printLog()
                self.shootOneShort()
                self.shootTwoThreeShorts()

            # else if (onlyShorts and not noShorts and not onlyLongs) or (InShortB and emaNearShort and not noShorts)
            elif (self.sm.onlyShort() and not self.sm.noShort() and not self.sm.onlyLong()) or (self.sm.fInShort and self.sm.emaNearShort(self.arVPShort) and not self.sm.noShort()):

                self.oBucket.flipShort = False
                self.oBucket.stopMoved = False
                self.printLog()
                self.shootOneShort()
                if not self.sm.onlyLong():
                    self.shootTwoThreeShorts()

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
