from ib_insync import MarketOrder, BracketOrder
from datetime import datetime, timedelta, time
from dateutil import tz
import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


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

    def timeInPosition(self, pos):
        # return minutes passed after fill
        fillTime = self.timeOf1Trade
        nowTime = datetime.now(tz=tz.tzlocal())
        return nowTime - fillTime

    def cancelAll(self):
        for opO in self.ib.openOrders():
            cancelTrade = self.ib.cancelOrder(opO)
            while not cancelTrade.isDone():
                self.ib.waitOnUpdate()
        # show open orders
        logging.info("---------------------------")
        logging.info('Should be no orders')
        logging.info(self.ib.openOrders())

    def closeAll(self):
        self.cancelAll()
        if self.ib.positions()[0].position > 0:
            # sell to close all
            mOrder = MarketOrder('SELL', self.ib.positions()[0].position, tif='GTC', outsideRth=True)
            closingTrade = self.ib.placeOrder(self.contract, mOrder)
            while not closingTrade.isDone():
                self.ib.waitOnUpdate()
        if self.ib.positions()[0].position < 0:
            # buy to close all
            mOrder = MarketOrder('BUY', abs(self.ib.positions()[0].position), tif='GTC', outsideRth=True)
            closingTrade = self.ib.placeOrder(self.contract, mOrder)
            while not closingTrade.isDone():
                self.ib.waitOnUpdate()
        # show open trades
        logging.info("---------------------------")
        logging.info('Should be no trades')
        logging.info(self.ib.openTrades())

    def __init__(self, ib, contract):
        self.ib = ib
        self.contract = contract

        # logging.info(self.ib.openOrders())

        # logging.info(self.ib.openTrades())

        self.firstLong = []
        self.secondLong = []
        self.thirdLong = []
        self.firstShort = []
        self.secondShort = []
        self.thirdShort = []

        self.rememberVPL = 0

        self.timeOf1Trade = datetime.now(tz=tz.tzlocal())
        self.timeOf2Trade = datetime.now(tz=tz.tzlocal())
        self.timeOf3Trade = datetime.now(tz=tz.tzlocal())

        self.flipLong = False
        self.flipShort = False
