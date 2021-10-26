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

        self.mylog.info("emaDiff")
        self.mylog.info(self.sm.emaDiff)

        self.mylog.info("---------------------------")

    def specialRound(self, pr):
        # rounded = round(pr*100)/100
        minTic = 0.25
        baseP = math.floor(pr)
        leftover = pr - baseP
        nums = math.floor(leftover/minTic)
        addToBase = minTic * nums
        return round(baseP + addToBase, 2)

    def shootOneLong(self, t1):
        self.mylog.info("Start Long1")
        lmpPrice = self.specialRound(self.arVPLong + t1)
        profPrice = self.specialRound(lmpPrice + 27)
        #profPrice0 = self.specialRound(lmpPrice + 27)

        stopPrice = self.specialRound(self.arVPLong - 20)

        bracket = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
        if t1 == 0:
            bracket.parent.orderType = 'MKT'

        for o in bracket:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setFirstLong(trade)
            self.mylog.info(o)

        #bracket0 = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice0, stopLossPrice=stopPrice, tif='GTC')
        # if t1 == 0:
        #    bracket0.parent.orderType = 'MKT'

        # for o in bracket0:
        #    trade = self.ib.placeOrder(self.contract, o)
        #    self.mylog.info(o)

        #beStop = self.arVPLong - 3
        # self.oBucket.rememberBEstop(self.specialRound(beStop))

        # remember level of entry
        self.oBucket.rememberVPLevel(self.specialRound(self.arVPLong))

    def shootTwoThreeLongs(self, t2, t3):
        lmpPrice2 = self.specialRound(self.arVPLong - t2)
        profPrice2 = self.specialRound(lmpPrice2 + 10)

        lmpPrice3 = self.specialRound(self.arVPLong - t3)
        profPrice3 = self.specialRound(lmpPrice3 + 14)

        stopPrice = self.specialRound(self.arVPLong - 20)

        #self.mylog.info("Start Long2")

        #bracket2 = self.ib.bracketOrder(action='BUY', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC')
        # for o in bracket2:
        #    trade = self.ib.placeOrder(self.contract, o)
        #    self.oBucket.setSecondLong(trade)
        #    self.mylog.info(o)

        self.mylog.info("Start Long3")

        bracket3 = self.ib.bracketOrder(action='BUY', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC')
        for o in bracket3:
            trade = self.ib.placeOrder(self.contract, o)
            self.oBucket.setThirdLong(trade)
            self.mylog.info(o)

        # remember B/E price
        # beStop = (lmpPrice2 + lmpPrice3)/2
        # self.oBucket.rememberBEstop(self.specialRound(beStop))

    def manageLongs(self):

        longBigTouch = self.arVPLong > 0 and self.arVPShort == 0 and self.vpTouches.countLongT() >= 1

        cond1 = self.sm.twoStepsFromHigh and self.sm.emaUp
        cond2 = (self.sm.wobbleCond or self.sm.trendCond or self.sm.strongCond or self.sm.extremeCond) and self.sm.emaDown

        noPosition = self.noPosition() and not (self.oBucket.firstLong or self.oBucket.firstShort)

        canLong = longBigTouch and noPosition

        if canLong and noPosition:
            self.oBucket.cancelAll()

            if cond1 or cond2:
                self.oBucket.flipLong = False
                self.oBucket.stopMoved = False
                self.oBucket.targetMoved = False

                self.printLog()

                if self.sm.emaDiff > -4 and self.sm.emaDiff < 0:
                    # Shoot All
                    self.shootOneLong(0)
                    self.shootTwoThreeLongs(13, 13)

                    if self.sm.extremeCond or self.sm.strongCond:
                        self.oBucket.rememberTimeDump()
                if self.sm.emaDiff > 0:
                    # Long 1
                    self.shootOneLong(0)
                    # Long 2 and 3
                    self.shootTwoThreeLongs(4, 6)
            elif self.sm.slowestCond or (self.sm.emaDiff > 1 and self.sm.oneStepsFromHigh):
                # Shoot All with diferent entries
                self.shootOneLong(0)
                self.shootTwoThreeLongs(4, 6)

        # Adjust orders

        # if self.hasLongPos() and self.oBucket.firstLong:
            # see if we need to close long
            #timeInLongTrade > 620 or (emaDiff < -2 and not fiveStepsFromHigh)
            # if self.oBucket.timeInPosition() > timedelta(minutes=620) or (self.sm.emaDiff < -2 and not self.sm.fiveStepsFromHigh):
                #rtClose = self.rtd.getiLoc(-1).close
                # self.mylog.info("rtClose")
                # self.mylog.info(rtClose)

                # if rtClose < self.oBucket.beStop - 5:
                #self.mylog.info("Trim position as it is bad.")
                # self.oBucket.closeAll()

        # check for no fill
        if self.oBucket.firstLong and self.noPosition() and self.oBucket.timeInPosition() > timedelta(minutes=180):
            self.oBucket.cancelAll()

    def manageShorts(self):

        shortBigTouch = self.arVPShort > 0 and self.arVPLong == 0 and self.vpTouches.countShortT() >= 1

        cond1 = self.sm.twoStepsFromLow and self.sm.emaDown and self.oBucket.timeSinceDumpOk()
        cond2 = (self.sm.wobbleCondS or self.sm.trendCondS or self.sm.strongCondS or self.sm.extremeCondS) and self.sm.emaUp and self.oBucket.timeSinceDumpOk()

        # close longs
        if self.hasLongPos() and self.oBucket.firstLong and shortBigTouch:
            if (cond1 or cond2):
                self.mylog.info("Close All Long, emaDiff")
                self.mylog.info(self.sm.emaDiff)
                if (self.sm.emaDiff < -0.7 or self.sm.trendCondS) and self.vpTouches.countShortT() >= 3:
                    # close all positions and cancel all orders
                    self.oBucket.closeAll()
            if self.sm.emaDiff < -5:
                # close all positions and cancel all orders
                self.oBucket.closeAll()

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
