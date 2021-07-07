from ib_insync import MarketOrder, LimitOrder, StopOrder
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

    def rememberTimeDump(self):
        self.timeDump = datetime.now(tz=tz.tzlocal())

    def timeSinceDumpOk(self):
        return datetime.now(tz=tz.tzlocal()) - self.timeDump >= timedelta(minutes=1441)

    def timeInPosition(self):
        # return minutes passed after fill
        fillTime = self.timeOf1Trade
        nowTime = datetime.now(tz=tz.tzlocal())
        # self.mylog.info("---------------------------")
        #self.mylog.info('Time in Position')
        #self.mylog.info(nowTime - fillTime)
        return nowTime - fillTime

    def cancelAll(self):
        if self.ib.openTrades() and (self.firstLong or self.firstShort):
            self.mylog.info("---------------------------")
            self.mylog.info('Cancel All')
            self.mylog.info(self.ib.openTrades())

            for opT in self.ib.openTrades():
                self.mylog.info(opT)
                if opT.orderStatus.status == 'Submitted' and not opT.fills:
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

    def adjustBraket(self, profitPrice, stopPrice):
        self.mylog.info("---------------------------")
        self.mylog.info('Adjust Braket')

        self.cancelAll()
        self.ib.sleep(5)
        # create OCA
        self.OCObraket(profitPrice, stopPrice)
        self.secondLong = []
        self.thirdLong = []
        self.secondShort = []
        self.thirdShort = []

    def OCObraket(self, profitPrice, stopPrice):
        self.mylog.info("---------------------------")
        self.mylog.info('OCO Braket')

        reverseAction = "BUY"
        if self.ib.positions()[0].position > 0:
            reverseAction = "SELL"

        quantity = abs(self.ib.positions()[0].position)

        takeProfit = LimitOrder(
            reverseAction, quantity, profitPrice,
            orderId=self.ib.client.getReqId(),
            transmit=True)
        stopLoss = StopOrder(
            reverseAction, quantity, stopPrice,
            orderId=self.ib.client.getReqId(),
            transmit=True)

        oco_id = self.ib.client.getReqId()

        oco = self.ib.oneCancelsAll([takeProfit, stopLoss], "OCO_" + str(oco_id), 1)

        for o in oco:
            self.ib.placeOrder(self.contract, o)

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
        self.targetMoved = False

        self.timeDump = datetime.now(tz=tz.tzlocal())

        self.timeOf1Trade = datetime.now(tz=tz.tzlocal())
        self.timeOf2Trade = datetime.now(tz=tz.tzlocal())
        self.timeOf3Trade = datetime.now(tz=tz.tzlocal())

        self.flipLong = False
        self.flipShort = False

        self.scale1Size = 1
        self.scale2Size = 1
        self.scale3Size = 1
