from ib_insync import MarketOrder, BracketOrder
from datetime import datetime, timedelta, time
from dateutil import tz
from orders_bucket import OrdersBucket
import math
import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class OrderManagement:
    def noPosition(self):
        return not self.ib.positions()
    # full pos, pending orders, cancel orders, tight stop
    # time in long trade, time in short trade

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
        logging.info("---------------------------")
        logging.info("Time Ok")
        logging.info(self.sm.timeIsOk())
        logging.info("onlyLong")
        logging.info(self.sm.onlyLong())
        logging.info("onlyShort")
        logging.info(self.sm.onlyShort())
        logging.info("positions")
        logging.info(self.ib.positions())
        logging.info("---------------------------")

    def specialRound(self, pr):
        #rounded = round(pr*100)/100
        minTic = 0.25
        baseP = math.floor(pr)
        leftover = pr - baseP
        nums = math.floor(leftover/minTic)
        addToBase = minTic * nums
        return round(baseP + addToBase, 2)

    def manageLongs(self):

        longBigTouch = self.arVPLong > 0 and self.arVPShort == 0 and self.vpTouches.countLongT() > 1

        # flip long
        # and not noLongs and (bigK < 10 or bigD < 10 or InLongB)
        if self.hasShortPos() and longBigTouch and not self.sm.noLong() and (self.sm.bigK() < 10 or self.sm.bigD() < 10 or self.sm.fInLong):
            # close all positions and cancer all orders
            self.oBucket.closeAll()
            self.oBucket.flipLong = True

        canLong = longBigTouch and self.noPosition() and not self.oBucket.firstLong and self.sm.timeIsOk()

        self.printLog()
        logging.info("---------------------------")
        logging.info("Long Big Touch")
        logging.info(longBigTouch)
        logging.info(canLong)
        logging.info("---------------------------")

        if (canLong or self.oBucket.flipLong) and self.sm.onlyLong() and not self.sm.noLong():
            # if (canTrade or flipLong) and onlyLongs and aroundVPLevel > 0 and aroundVPLevelToShort == 0 and not noLongs
            self.oBucket.flipLong = False
            logging.info("Start Long1 ")
            lmpPrice = self.specialRound(self.arVPLong + 1)
            profPrice = self.specialRound(lmpPrice + 10)
            stopPrice = self.specialRound(lmpPrice - 23)
            bracket = self.ib.bracketOrder(action='BUY', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC', outsideRth=True)
            for o in bracket:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setFirstLong(trade)

            logging.info("Start Long2 ")
            lmpPrice2 = self.specialRound(self.arVPLong - 4)
            profPrice2 = self.specialRound(lmpPrice2 + 10)
            bracket2 = self.ib.bracketOrder(action='BUY', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC', outsideRth=True)
            for o in bracket2:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setSecondLong(trade)

            logging.info("Start Long3 ")
            lmpPrice3 = self.specialRound(self.arVPLong - 10)
            profPrice3 = self.specialRound(lmpPrice3 + 20)
            bracket3 = self.ib.bracketOrder(action='BUY', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC', outsideRth=True)
            for o in bracket3:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setThirdLong(trade)

            self.oBucket.rememberVPLevel(self.specialRound(self.arVPLong))

            logging.info("---------------------------")
            logging.info("Long Order Prices")
            logging.info(lmpPrice)
            logging.info(profPrice)
            logging.info(stopPrice)
            logging.info(self.rtd.getiLoc(-1))
            logging.info("---------------------------")

    def manageShorts(self):

        shortBigTouch = self.arVPShort > 0 and self.arVPLong == 0 and self.vpTouches.countShortT() > 1

        # flip short
        # and not noShorts and onlyShorts
        if self.hasLongPos() and shortBigTouch and not self.sm.noShort() and self.sm.onlyShort():
            # close all positions and cancer all orders
            self.oBucket.closeAll()
            self.oBucket.flipShort = True

        canShort = shortBigTouch and self.noPosition() and not self.oBucket.firstShort and self.sm.timeIsOk()

        logging.info("---------------------------")
        self.printLog()
        logging.info("Short Big Touch")
        logging.info(shortBigTouch)
        logging.info(canShort)
        logging.info("---------------------------")

        if (canShort or self.oBucket.flipShort) and self.sm.onlyShort() and not self.sm.noShort():
            # and onlyShorts and aroundVPLevelToShort > 0 and aroundVPLevel == 0 and not noShorts
            self.oBucket.flipShort = False

            logging.info("Start Short")
            lmpPrice = self.specialRound(self.arVPShort - 1)
            profPrice = self.specialRound(lmpPrice - 10)
            stopPrice = self.specialRound(lmpPrice + 23)
            bracket = self.ib.bracketOrder(action='SELL', quantity=self.scale1Size, limitPrice=lmpPrice, takeProfitPrice=profPrice, stopLossPrice=stopPrice, tif='GTC', outsideRth=True)
            for o in bracket:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setFirstShort(trade)

            logging.info("Start Short2")
            lmpPrice2 = self.specialRound(self.arVPShort + 3)
            profPrice2 = self.specialRound(lmpPrice2 - 10)
            bracket2 = self.ib.bracketOrder(action='SELL', quantity=self.scale2Size, limitPrice=lmpPrice2, takeProfitPrice=profPrice2, stopLossPrice=stopPrice, tif='GTC', outsideRth=True)
            for o in bracket2:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setSecondShort(trade)

            logging.info("Start Short3")
            lmpPrice3 = self.specialRound(self.arVPShort + 10)
            profPrice3 = self.specialRound(lmpPrice3 - 20)
            bracket3 = self.ib.bracketOrder(action='SELL', quantity=self.scale3Size, limitPrice=lmpPrice3, takeProfitPrice=profPrice3, stopLossPrice=stopPrice, tif='GTC', outsideRth=True)
            for o in bracket3:
                trade = self.ib.placeOrder(self.contract, o)
                self.oBucket.setThirdShort(trade)

            self.oBucket.rememberVPLevel(self.specialRound(self.arVPShort))
            logging.info("---------------------------")
            logging.info("Short Order Prices")
            logging.info(lmpPrice)
            logging.info(profPrice)
            logging.info(stopPrice)
            logging.info(self.rtd.getiLoc(-1))
            logging.info("---------------------------")

    def goDoBusiness(self):
        # if self.ib.positions() != []:
        # logging.info(self.ib.positions())

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

    def __init__(self, ib, contract, sm, oBucket, rtd, vpTouches):
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
