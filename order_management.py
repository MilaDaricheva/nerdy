from ib_insync import MarketOrder, BracketOrder
from datetime import datetime, timedelta, time
from dateutil import tz
from orders_bucket import OrdersBucket
import math
#import logging
#import logging.handlers as handlers

#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


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
        self.mylog.info("Time Ok")
        self.mylog.info(self.sm.timeIsOk())

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
        #rounded = round(pr*100)/100
        minTic = 0.25
        baseP = math.floor(pr)
        leftover = pr - baseP
        nums = math.floor(leftover/minTic)
        addToBase = minTic * nums
        return round(baseP + addToBase, 2)

    def manageLongs(self):

        if self.oBucket.firstLong and self.hasLongPos():
            sevenHours = timedelta(hours=7)
            if self.oBucket.timeInPosition() > sevenHours:
                self.mylog.info("---------------------------")
                self.mylog.info("Long Trade Takes too long")
                # move stops to b/e
                self.oBucket.moveStops(self.oBucket.beStop)

        longBigTouch = self.arVPLong > 0 and self.arVPShort == 0 and self.vpTouches.countLongT() > 1

        # flip long, close short
        # and ((not noLongs and (bigK < 10 or bigD < 10 or InLongB)) or emaUp)
        if self.hasShortPos() and self.oBucket.firstShort and longBigTouch and ((not self.sm.noLong() and (self.sm.bigK() < 10 or self.sm.bigD() < 10 or self.sm.fInLong)) or self.sm.emaUp()):
            # close all positions and cancer all orders
            self.oBucket.closeAll()
            self.oBucket.flipLong = True

        canLong = longBigTouch and self.noPosition() and not self.oBucket.firstLong and self.sm.timeIsOk()

        # vself.printLog()
        # self.mylog.info("---------------------------")
        # self.mylog.info("Long Big Touch")
        # self.mylog.info(longBigTouch)
        # self.mylog.info(canLong)
        # self.mylog.info("---------------------------")

        if (canLong or self.oBucket.flipLong) and not self.oBucket.firstLong and ((self.sm.onlyLong() and not self.sm.noLong()) or self.sm.emaUp()):
            # if (canTrade or flipLong) and aroundVPLevel > 0 and aroundVPLevelToShort == 0 and ((onlyLongs and not noLongs) or emaUp)
            self.oBucket.flipLong = False
            self.printLog()

            self.mylog.info("Start Long1")
            lmpPrice = self.specialRound(self.arVPLong + 1)
            profPrice = self.specialRound(lmpPrice + 75)
            stopPrice = self.specialRound(lmpPrice - 23)
            bracket = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
            bracket.parent.orderType = 'MKT'
            for o in bracket:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setFirstLong(trade)

            self.mylog.info("Start Long2")
            lmpPrice2 = self.specialRound(self.arVPLong - 4)
            profPrice2 = self.specialRound(lmpPrice2 + 10)
            bracket2 = self.ib.bracketOrder(action='BUY', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC')
            for o in bracket2:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setSecondLong(trade)

            self.mylog.info("Start Long3")
            lmpPrice3 = self.specialRound(self.arVPLong - 10)
            profPrice3 = self.specialRound(lmpPrice3 + 20)
            bracket3 = self.ib.bracketOrder(action='BUY', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC')
            for o in bracket3:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setThirdLong(trade)

            self.oBucket.rememberVPLevel(self.specialRound(self.arVPLong))

            beStop = (lmpPrice + lmpPrice2 + lmpPrice3)/3
            self.oBucket.rememberBEstop(self.specialRound(beStop))

            # self.mylog.info("---------------------------")
            #self.mylog.info("Long Order Prices")
            # self.mylog.info(lmpPrice)
            # self.mylog.info(profPrice)
            # self.mylog.info(stopPrice)
            # self.mylog.info(self.rtd.getiLoc(-1))
            # self.mylog.info("---------------------------")

    def manageShorts(self):

        if self.oBucket.firstShort and self.hasShortPos():
            sevenHours = timedelta(hours=7)
            if self.oBucket.timeInPosition() > sevenHours:
                self.mylog.info("---------------------------")
                self.mylog.info("Short Trade Takes too long")
                # move stops to b/e
                self.oBucket.moveStops(self.oBucket.beStop)

        shortBigTouch = self.arVPShort > 0 and self.arVPLong == 0 and self.vpTouches.countShortT() > 1

        # flip short, close longs
        # and ((not noShorts and onlyShorts) or emaDown)
        if self.hasLongPos() and self.oBucket.firstLong and shortBigTouch and ((not self.sm.noShort() and self.sm.onlyShort()) or self.sm.emaDown()):
            # if not (emaUp and onlyLongs)
            if not (self.sm.emaUp() and self.sm.onlyLong()):
                # close all positions and cancer all orders
                self.oBucket.closeAll()
                self.oBucket.flipShort = True

        canShort = shortBigTouch and self.noPosition() and not self.oBucket.firstShort and self.sm.timeIsOk()

        # self.mylog.info("---------------------------")
        # self.printLog()
        #self.mylog.info("Short Big Touch")
        # self.mylog.info(shortBigTouch)
        # self.mylog.info(canShort)
        # self.mylog.info("---------------------------")

        if (canShort or self.oBucket.flipShort) and not self.oBucket.firstShort and ((self.sm.onlyShort() and not self.sm.noShort()) or self.sm.emaDown()):
            # and ((not noShorts and onlyShorts) or emaDown)
            if not (self.sm.emaUp() and self.sm.onlyLong()):
                # if not (emaUp and onlyLongs)
                self.oBucket.flipShort = False
                self.printLog()
                self.mylog.info("Start Short")
                lmpPrice = self.specialRound(self.arVPShort - 1)
                profPrice = self.specialRound(lmpPrice - 35)
                stopPrice = self.specialRound(lmpPrice + 23)
                bracket = self.ib.bracketOrder(action='SELL', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC')
                bracket.parent.orderType = 'MKT'
                for o in bracket:
                    trade = self.ib.placeOrder(self.contract, o)
                    self.oBucket.setFirstShort(trade)

                self.mylog.info("Start Short2")
                lmpPrice2 = self.specialRound(self.arVPShort + 3)
                profPrice2 = self.specialRound(lmpPrice2 - 10)
                bracket2 = self.ib.bracketOrder(action='SELL', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC')
                for o in bracket2:
                    trade = self.ib.placeOrder(self.contract, o)
                    self.oBucket.setSecondShort(trade)

                self.mylog.info("Start Short3")
                lmpPrice3 = self.specialRound(self.arVPShort + 10)
                profPrice3 = self.specialRound(lmpPrice3 - 20)
                bracket3 = self.ib.bracketOrder(action='SELL', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC')
                for o in bracket3:
                    trade = self.ib.placeOrder(self.contract, o)
                    self.oBucket.setThirdShort(trade)

                self.oBucket.rememberVPLevel(self.specialRound(self.arVPShort))

                beStop = (lmpPrice + lmpPrice2 + lmpPrice3)/3
                self.oBucket.rememberBEstop(self.specialRound(beStop))
                # self.mylog.info("---------------------------")
                #self.mylog.info("Short Order Prices")
                # self.mylog.info(lmpPrice)
                # self.mylog.info(profPrice)
                # self.mylog.info(stopPrice)
                # self.mylog.info(self.rtd.getiLoc(-1))
                # self.mylog.info("---------------------------")

    def goDoBusiness(self):
        # if self.ib.positions() != []:
        # self.mylog.info(self.ib.positions())

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
