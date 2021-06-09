from ib_insync import MarketOrder, BracketOrder
from datetime import datetime, timedelta, time
from dateutil import tz
#import logging
#import logging.handlers as handlers

#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class OrdersBucket:

    def setFirstLong(self, trade):
        self.firstLong.append(trade)
        self.timeOf1Trade = datetime.now(tz=tz.tzlocal())

    def setFirstShort(self, trade):
        self.firstShort.append(trade)
        self.timeOf1Trade = datetime.now(tz=tz.tzlocal())

    def setSecondLong(self, trade):
        self.secondLong.append(trade)
        self.timeOf2Trade = datetime.now(tz=tz.tzlocal())

    def setSecondShort(self, trade):
        self.secondShort.append(trade)
        self.timeOf2Trade = datetime.now(tz=tz.tzlocal())

    def setThirdLong(self, trade):
        self.thirdLong.append(trade)
        self.timeOf3Trade = datetime.now(tz=tz.tzlocal())

    def setThirdShort(self, trade):
        self.thirdShort.append(trade)
        self.timeOf3Trade = datetime.now(tz=tz.tzlocal())

    def rememberVPLevel(self, level):
        self.rememberVPL = level

    def rememberBEstop(self, level):
        self.beStop = level

    def timeInPosition(self):
        # return minutes passed after fill
        fillTime = self.timeOf1Trade
        nowTime = datetime.now(tz=tz.tzlocal())
        # self.mylog.info("---------------------------")
        #self.mylog.info('Time in Position')
        #self.mylog.info(nowTime - fillTime)
        return nowTime - fillTime

    def cancel3d(self, direction):
        self.mylog.info("---------------------------")
        self.mylog.info('Cancel 3d')

        if direction > 0 and self.thirdLong:
            for tr in self.thirdLong:
                if tr.orderStatus.status == 'Submitted':
                    self.mylog.info('Sending Cancel to 3d scale')
                    self.ib.cancelOrder(tr.order)
            self.thirdLong = []
            self.secondLong = []

        if direction < 0 and self.thirdShort:
            for tr in self.thirdShort:
                if tr.orderStatus.status == 'Submitted':
                    self.mylog.info('Sending Cancel to 3d scale')
                    self.ib.cancelOrder(tr.order)
            self.thirdShort = []
            self.secondShort = []

    def cancelAll(self):
        if self.ib.openTrades() and (self.firstLong or self.firstShort):
            self.mylog.info("---------------------------")
            self.mylog.info('Cancel All')
            self.mylog.info(self.ib.openTrades())

            for opT in self.ib.openTrades():
                if opT.orderStatus.status == 'Submitted':
                    self.mylog.info('Sending Cancel')
                    self.ib.cancelOrder(opT.order)

            # show open orders
            # self.mylog.info("---------------------------")
            #self.mylog.info('Should be no orders')
            # self.mylog.info(self.ib.openOrders())

    def closeAll(self):
        self.cancelAll()
        # self.ib.sleep(5)
        self.mylog.info("---------------------------")
        self.mylog.info('Close All')

        if self.ib.positions()[0].position > 0 and self.firstLong:
            # sell to close all
            mOrder = MarketOrder('SELL', self.ib.positions()[0].position, tif='GTC')
            self.ib.placeOrder(self.contract, mOrder)

        if self.ib.positions()[0].position < 0 and self.firstShort:
            # buy to close all
            mOrder = MarketOrder('BUY', abs(self.ib.positions()[0].position), tif='GTC')
            self.ib.placeOrder(self.contract, mOrder)

        self.firstLong = []
        self.secondLong = []
        self.thirdLong = []
        self.firstShort = []
        self.secondShort = []
        self.thirdShort = []

    def moveStops(self, level):
        self.mylog.info("---------------------------")
        self.mylog.info('Move Stops')

        self.ib.sleep(10)

        for opT in self.ib.openTrades():
            if opT.orderStatus.status == 'PreSubmitted' and opT.order.auxPrice > 0:
                opT.order.triggerPrice = level
                opT.order.adjustedStopPrice = level
                self.ib.placeOrder(self.contract, opT.order)

    def __init__(self, ib, contract, logger):
        self.mylog = logger
        self.ib = ib
        self.contract = contract

        # self.mylog.info(self.ib.openOrders())

        # self.mylog.info(self.ib.openTrades())

        self.firstLong = []
        self.secondLong = []
        self.thirdLong = []
        self.firstShort = []
        self.secondShort = []
        self.thirdShort = []

        self.rememberVPL = 0
        self.beStop = 0
        self.stopMoved = False

        self.timeOf1Trade = datetime.now(tz=tz.tzlocal())
        self.timeOf2Trade = datetime.now(tz=tz.tzlocal())
        self.timeOf3Trade = datetime.now(tz=tz.tzlocal())

        self.flipLong = False
        self.flipShort = False

        self.scale1Size = 1
        self.scale2Size = 1
        self.scale3Size = 1
