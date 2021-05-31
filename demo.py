from ta.utils import dropna
from ib_insync import IB, Future, util
from hist_data import HistData
from hist_data_fetcher import HistDataFetcher
from rt_data import RealTimeData
from strategy_management import StrategyManagement
from order_management import OrderManagement
from orders_bucket import OrdersBucket
from vp_touches import VpTouches
from datetime import datetime, timedelta, time
from dateutil import tz
import logging
import logging.handlers as handlers

import nest_asyncio

nest_asyncio.apply()


class AlgoVP:
    def setUpHistData(self):
        self.mylog.info("---------------------------")
        self.mylog.info("reqHistoricalData...")
        self.hist_data_fetcher = HistDataFetcher(self.mylog, self.clientID)
        self.min_data = self.hist_data_fetcher.getMinData()

    def setUpData(self):
        self.mylog.info("---------------------------")
        self.mylog.info("setUpData")

        self.setUpHistData()

        self.rt_bars = None
        self.rt_bars = self.ib.reqRealTimeBars(self.contract, 5, 'MIDPOINT', False)
        self.rt_bars.updateEvent += self.onRTBarUpdate

    def onPositionChange(self, trade, fill):
        self.mylog.info("---------------------------")
        self.mylog.info("Position Change")
        self.mylog.info(trade)
        self.mylog.info(fill)

        if trade.order.action == 'BUY' and not self.ib.positions():
            # short closed
            self.mylog.info("short closed")
            self.oBucket.cancelAll()
        if trade.order.action == 'SELL' and not self.ib.positions():
            # long closed
            self.mylog.info("long closed")
            self.oBucket.cancelAll()

        if trade.order.action == 'BUY' and self.ib.positions():
            # scale out of short happened
            if self.ib.positions()[0].position == -self.oBucket.scale1Size:
                self.mylog.info("scale out of 2d short happened - no 3d filled")
                # cancel 3d scale, move stops be
                self.mylog.info("cancel 3d short")
                self.oBucket.cancel3d(-1)
                self.oBucket.moveStops(self.oBucket.beStop)
            if self.ib.positions()[0].position == -(self.oBucket.scale1Size + self.oBucket.scale3Size):
                self.mylog.info("scale out of 2d short happened - 3d did fill")
                # move stops tighter
                self.mylog.info("move stops BE+10")
                self.oBucket.moveStops(self.oBucket.beStop + 10)

        if trade.order.action == 'SELL' and self.ib.positions():
            # scale out of long happened
            if self.ib.positions()[0].position == self.oBucket.scale1Size:
                self.mylog.info("scale out of 2d long happened - no 3d filled")
                # cancel 3d scale, move stops be
                self.mylog.info("cancel 3d long")
                self.oBucket.cancel3d(1)
                self.oBucket.moveStops(self.oBucket.beStop)
            if self.ib.positions()[0].position == self.oBucket.scale1Size + self.oBucket.scale3Size:
                self.mylog.info("scale out of 2d long happened - 3d did fill")
                # move stops tighter
                self.mylog.info("move stops BE-10 ")
                self.oBucket.moveStops(self.oBucket.beStop - 10)

    def onErrorEvent(self, reqId, errorCode, errorString, contract):
        self.mylog.info("---------------------------")
        self.mylog.info("My error handler here")
        self.mylog.info(errorCode)
        self.mylog.info(errorString)
        if errorCode == 2105:
            self.mylog.info("disconnect")
            self.ib.disconnect()

    def onConnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connected Event")

    def onDisconnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Disconnected Event")
        #now_time = datetime.now(tz=tz.tzlocal())
        #open_time = datetime(now_time.year, now_time.month, now_time.day, 18, 2, 0, 0, tz.tzlocal())
        #util.schedule(open_time, self.connectAfterOpen)

    def connectAfterOpen(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connect After Open")
        if not self.ib.isConnected():
            self.mylog.info("Connecting...")
            self.ib.connect('127.0.0.1', 7496, clientId=1)

    def timeToClose(self):
        now_time = datetime.now(tz=tz.tzlocal())
        close_time = datetime(now_time.year, now_time.month, now_time.day, 16, 10, 0, 0, tz.tzlocal())
        twoSec = timedelta(seconds=2)

        if now_time < close_time + twoSec and now_time > close_time - twoSec:
            return True
        else:
            return False

    def timeIsOk(self):
        now_time = datetime.now(tz=tz.tzlocal())
        eod_time = datetime(now_time.year, now_time.month, now_time.day, 16, 0, 0, 0, tz.tzlocal())
        night_time = datetime(now_time.year, now_time.month, now_time.day, 18, 5, 0, 0, tz.tzlocal())

        if now_time < eod_time or now_time > night_time:
            return True
        else:
            return False

    def onRTBarUpdate(self, bars, hasNewBar):
        # new real time 5sec bar
        if hasNewBar:
            self.mylog.info("rt data")
            self.mylog.info(bars[-1])

            self.min_data = self.hist_data_fetcher.getMinData()

            cuttentBarTime = bars[-1].time.astimezone(tz.tzutc())
            nowTime = datetime.now(tz=tz.tzutc())

            histBarTime = self.min_data.timeCreated
            self.mylog.info(histBarTime)

            twSec = timedelta(seconds=20)
            twoMin = timedelta(minutes=2)

            rtDataOk = nowTime - twSec <= cuttentBarTime
            histDataOk = nowTime - twoMin <= histBarTime

            if self.timeToClose() and self.ib.isConnected():
                self.oBucket.closeAll()
                self.ib.disconnect()

            if histDataOk and rtDataOk and self.timeIsOk():
                rtd = RealTimeData(bars, self.min_data, self.vp_levels, self.mylog)
                sm = StrategyManagement(bars, self.min_data, self.vp_levels, self.mylog)
                om = OrderManagement(self.ib, self.contract, sm, self.oBucket, rtd, self.vpTouches, self.mylog)
                om.goDoBusiness()

    def __init__(self):
        # set logger
        logger = logging.getLogger('my_app')
        logger.setLevel(logging.INFO)

        logHandler = handlers.RotatingFileHandler('app.log', maxBytes=3*1024*1024, backupCount=2)
        logHandler.setLevel(logging.INFO)
        logger.addHandler(logHandler)

        self.mylog = logger

        self.connectionStarted = datetime.now(tz=tz.tzlocal())

        self.mylog.info("---------------------------")
        self.mylog.info("Building VP Levels")

        # main vp levels
        self.vp_levels = []
        num_vp = 50
        sVP = 3880.51

        for i in range(num_vp):
            nextVP = round(sVP+13.065*i, 2)
            self.vp_levels.append(nextVP)

        # set IB
        self.mylog.info("---------------------------")
        self.mylog.info("Starting the connection")

        self.clientID = 2

        self.ib = IB()

        self.ib.connect('127.0.0.1', 7496, clientId=1)

        self.contract = Future('MES', '20210618', 'GLOBEX', 'MESM1', '5', 'USD')
        self.ib.qualifyContracts(self.contract)

        if self.ib.isConnected():
            self.setUpData()

        self.oBucket = OrdersBucket(self.ib, self.contract, self.mylog)
        self.vpTouches = VpTouches(self.mylog)

        self.ib.connectedEvent += self.onConnectedEvent

        self.ib.disconnectedEvent += self.onDisconnectedEvent

        self.ib.errorEvent += self.onErrorEvent

        self.ib.execDetailsEvent += self.onPositionChange

        self.ib.run()


startAlgo = AlgoVP()
