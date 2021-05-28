from ta.utils import dropna
from ib_insync import IB, Future, util
from hist_data import HistData
from rt_data import RealTimeData
from strategy_management import StrategyManagement
from order_management import OrderManagement
from orders_bucket import OrdersBucket
from vp_touches import VpTouches
from datetime import datetime, timedelta, time
from dateutil import tz
import logging
import logging.handlers as handlers
from ib_insync import IBC, Watchdog

import nest_asyncio

nest_asyncio.apply()

#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class AlgoVP:
    def setUpHistData(self):
        self.min_bars = None
        self.min_data = None

        self.min_bars = self.ib.reqHistoricalData(
            self.contract, endDateTime='', durationStr='2 D',
            barSizeSetting='1 min', whatToShow='MIDPOINT', useRTH=False,
            formatDate=1,
            keepUpToDate=True)

        self.min_data = HistData(self.min_bars, self.mylog)
        self.min_data.printLastN(4)

        self.min_bars.updateEvent += self.onMinBarUpdate

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
            self.min_bars = None
            self.min_data = None
        if errorCode == 2106 and not self.min_bars:
            self.setUpHistData()

    def onConnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connected Event")
        self.setUpData()

    def connectAfterOpen(self):
        self.ib.connect('127.0.0.1', 7496, clientId=1)

    def onMinBarUpdate(self, bars, hasNewBar):
        # update 1min bars
        if hasNewBar:
            u_min_data = HistData(bars, self.mylog)
            self.min_data = u_min_data
            self.mylog.info(bars[-1])

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
            #self.mylog.info("Time Game")
            # UTC
            cuttentBarTime = bars[-1].time.astimezone(tz.tzutc())
            nowTime = datetime.now(tz=tz.tzutc())
            histBarTime = self.min_data.timeCreated

            twSec = timedelta(seconds=20)
            twoMin = timedelta(minutes=2)

            rtDataOk = nowTime - twSec <= cuttentBarTime
            histDataOk = nowTime - twoMin <= histBarTime

            if self.timeToClose() and self.ib.isConnected():
                self.oBucket.closeAll()
                self.ib.disconnect()

            if histDataOk:
                if rtDataOk:
                    if self.timeIsOk():
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

        self.ib = IB()

        self.ib.connect('127.0.0.1', 7496, clientId=1)

        self.contract = Future('MES', '20210618', 'GLOBEX', 'MESM1', '5', 'USD')
        self.ib.qualifyContracts(self.contract)

        if self.ib.isConnected():
            self.setUpData()

        self.oBucket = OrdersBucket(self.ib, self.contract, self.mylog)
        self.vpTouches = VpTouches(self.mylog)

        self.ib.connectedEvent += self.onConnectedEvent

        self.ib.errorEvent += self.onErrorEvent

        self.ib.execDetailsEvent += self.onPositionChange

        now_time = datetime.now(tz=tz.tzlocal())
        open_time = datetime(now_time.year, now_time.month, now_time.day, 18, 2, 0, 0, tz.tzlocal())
        util.schedule(open_time, self.connectAfterOpen)

        self.ib.run()


startAlgo = AlgoVP()
