from ib_insync import MarketOrder, LimitOrder, StopOrder
from datetime import datetime, timedelta, time
from dateutil import tz

#import asyncio


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

            #loop = asyncio.get_event_loop()
            #cancelDelay = 1

            for opT in self.ib.openTrades():
                self.mylog.info(opT)
                self.mylog.info(opT.contract.symbol)
                self.mylog.info(opT.isDone())
                self.mylog.info(opT.order.ocaGroup)
                self.mylog.info(opT.order.orderType)
                self.mylog.info(opT.orderStatus.status)

                if opT.orderStatus.status == 'Submitted' and not opT.fills and opT.contract.symbol == 'MES':
                    self.mylog.info('Sending Cancel')
                    #loop.run_until_complete(self.shootCancel(opT.order, cancelDelay))
                    self.ib.cancelOrder(opT.order)
                    #cancelDelay += 1
                    # self.ib.cancelOrder(opT.order)
                if opT.order.ocaGroup and not opT.fills and opT.contract.symbol == 'MES':
                    self.mylog.info('Sending Cancel for OCA Group')
                    #loop.run_until_complete(self.shootCancel(opT.order, cancelDelay))
                    self.ib.cancelOrder(opT.order)
                    #cancelDelay += 1
                    # self.ib.cancelOrder(opT.order)

            # loop.close()

    def emptyPosObject(self):
        self.firstLong = []
        self.secondLong = []
        self.thirdLong = []
        self.firstShort = []
        self.secondShort = []
        self.thirdShort = []

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

        self.emptyPosObject()

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

        self.mylog.info(profitPrice)
        self.mylog.info(stopPrice)

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

    def adjustTarget(self, newT):
        self.mylog.info("---------------------------")
        self.mylog.info('New Target')
        self.mylog.info(newT)

        for opT in self.ib.openTrades():
            self.mylog.info(opT.order.orderId)
            self.mylog.info(self.firstLong[1].order.orderId)
            if opT.order.orderId == self.firstLong[1].order.orderId:
                self.mylog.info('Setting New Target')
                self.firstLong[1].order.lmtPrice = self.rememberVPL + 75
                self.ib.placeOrder(self.contract, self.firstLong[1].order)

    def adjustTargetShort(self, newT):
        self.mylog.info("---------------------------")
        self.mylog.info('New Target Short')
        self.mylog.info(newT)

        for opT in self.ib.openTrades():
            self.mylog.info(opT.order.orderId)
            self.mylog.info(self.firstShort[1].order.orderId)
            if opT.order.orderId == self.firstShort[1].order.orderId:
                self.mylog.info('Setting New Target')
                self.firstShort[1].order.lmtPrice = self.rememberVPL - 75
                self.ib.placeOrder(self.contract, self.firstShort[1].order)

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
