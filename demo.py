#from ta.utils import dropna
from ib_insync import IB, Future, util
from hist_data_fetcher import HistDataFetcher
from rt_data import RealTimeData
from strategy_management import StrategyManagement
from order_management import OrderManagement
from orders_bucket import OrdersBucket
from vp_touches import VpTouches
from datetime import datetime, timedelta
from dateutil import tz
import logging
import logging.handlers as handlers

import nest_asyncio
nest_asyncio.apply()


class AlgoVP:
    def reConnect(self):
        self.mylog.info("---------------------------")
        self.mylog.info("reConnect")
        if not self.ib.isConnected():
            self.ib.connect('127.0.0.1', 7496, clientId=1)

    def setUpHistData(self):
        if not self.hist_data_fetcher:
            self.mylog.info("---------------------------")
            self.mylog.info("setUpHistData + deadZone")
            self.deadZone()
            self.mylog.info(self.clientID)
            self.hist_data_fetcher = HistDataFetcher(self.mylog, self.clientID)

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
                # self.oBucket.moveStops(self.oBucket.beStop)
            if self.ib.positions()[0].position == -(self.oBucket.scale1Size + self.oBucket.scale3Size):
                self.mylog.info("scale out of 2d short happened - 3d did fill")
                # move stops tighter
                self.mylog.info("move stops BE+10")
                #self.oBucket.moveStops(self.oBucket.beStop + 10)

        if trade.order.action == 'SELL' and self.ib.positions():
            # scale out of long happened
            if self.ib.positions()[0].position == self.oBucket.scale1Size:
                self.mylog.info("scale out of 2d long happened - no 3d filled")
                # cancel 3d scale, move stops be
                self.mylog.info("cancel 3d long")
                self.oBucket.cancel3d(1)
                # self.oBucket.moveStops(self.oBucket.beStop)
            if self.ib.positions()[0].position == self.oBucket.scale1Size + self.oBucket.scale3Size:
                self.mylog.info("scale out of 2d long happened - 3d did fill")
                # move stops tighter
                self.mylog.info("move stops BE-10 ")
                #self.oBucket.moveStops(self.oBucket.beStop - 10)

    def onErrorEvent(self, reqId, errorCode, errorString, contract):
        self.mylog.info("---------------------------")
        self.mylog.info("My error handler here")
        self.mylog.info(errorCode)
        self.mylog.info(errorString)

        now_time = datetime.now(tz=tz.tzlocal())
        timeDelta = timedelta(minutes=2)
        open_time = now_time + timeDelta

        timeGap = now_time - self.requestStarted >= timeDelta
        if errorCode == 162:
            self.ib.disconnect()
            self.doNotConnect = True
        if (errorCode == 2105 or errorCode == 1100) and self.hist_data_fetcher:
            self.mylog.info("Hist data nah nah")
            self.hist_data_fetcher.killFetcher()
            self.hist_data_fetcher = None
            self.clientID = self.clientID + 1
        if (errorCode == 2106 or errorCode == 1101 or errorCode == 1102) and not self.hist_data_fetcher and timeGap:
            self.mylog.info("Hist data seems ok")
            self.requestStarted = datetime.now(tz=tz.tzlocal())
            util.schedule(open_time, self.setUpHistData)

    def onConnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connected Event")

    def onDisconnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Disconnected Event")
        now_time = datetime.now(tz=tz.tzlocal())
        timeDelta = timedelta(minutes=5)
        open_time = now_time + timeDelta

        if not self.doNotConnect:
            util.schedule(open_time, self.reConnect)

    def timeToClose(self):
        now_time = datetime.now(tz=tz.tzlocal())
        close_time_from = datetime(now_time.year, now_time.month, now_time.day, 16, 10, 0, 0, tz.tzlocal())
        close_time_to = datetime(now_time.year, now_time.month, now_time.day, 16, 59, 0, 0, tz.tzlocal())

        if now_time < close_time_to and now_time > close_time_from:
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

    def deadZone(self):
        now_time = datetime.now(tz=tz.tzlocal())
        start_time = datetime(now_time.year, now_time.month, now_time.day, 0, 0, 0, 0, tz.tzlocal())
        end_time = datetime(now_time.year, now_time.month, now_time.day, 0, 30, 0, 0, tz.tzlocal())
        deadZone = now_time < end_time and now_time > start_time

        if deadZone:
            return True
        else:
            return False

    def onRTBarUpdate(self, bars, hasNewBar):
        # new real time 5sec bar
        if hasNewBar:
            #self.mylog.info("rt data")
            # self.mylog.info(bars[-1])

            #now_time = datetime.now(tz=tz.tzlocal())
            #timeDelta = timedelta(minutes=5)
            timeGap = datetime.now(tz=tz.tzlocal()) - self.requestStarted >= timedelta(minutes=5)

            if self.timeToClose() and (self.oBucket.firstLong or self.oBucket.firstShort):
                self.mylog.info("---------------------------")
                self.mylog.info("timeToClose")
                self.oBucket.closeAll()
                # historical data?
                self.hist_data_fetcher.killFetcher()
                self.hist_data_fetcher = None
                self.clientID = self.clientID + 1

            if self.timeIsOk() and not self.deadZone():
                if not self.hist_data_fetcher:
                    if timeGap:
                        self.mylog.info("---------------------------")
                        self.mylog.info("No fetcher, create one")
                        self.requestStarted = datetime.now(tz=tz.tzlocal())
                        self.setUpHistData()
                else:
                    self.min_data = self.hist_data_fetcher.getMinData()

                    cuttentBarTime = bars[-1].time.astimezone(tz.tzutc())
                    nowTime = datetime.now(tz=tz.tzutc())

                    histBarTime = self.min_data.timeCreated
                    # self.mylog.info("self.min_data.timeCreated")
                    # self.mylog.info(histBarTime)

                    twSec = timedelta(seconds=20)
                    twoMin = timedelta(minutes=2)

                    rtDataOk = nowTime - twSec <= cuttentBarTime
                    histDataOk = nowTime - twoMin <= histBarTime

                    if histDataOk and rtDataOk:
                        #self.mylog.info("all data ok")
                        # self.mylog.info(nowTime)
                        rtd = RealTimeData(bars, self.min_data, self.vp_levels, self.mylog)
                        sm = StrategyManagement(bars, self.min_data, self.vp_levels, self.mylog)
                        om = OrderManagement(self.ib, self.contract, sm, self.oBucket, rtd, self.vpTouches, self.mylog)
                        om.goDoBusiness()
                    else:
                        if timeGap and not histDataOk:
                            self.mylog.info("---------------------------")
                            self.mylog.info("Hist Data not OK, kill fetcher, UTC Time")
                            self.mylog.info(nowTime)
                            self.hist_data_fetcher.killFetcher()
                            self.hist_data_fetcher = None
                            self.clientID = self.clientID + 1

    def __init__(self):
        # set logger
        logger = logging.getLogger('my_app')
        logger.setLevel(logging.INFO)

        logHandler = handlers.RotatingFileHandler('app.log', maxBytes=3*1024*1024, backupCount=2)
        logHandler.setLevel(logging.INFO)
        logger.addHandler(logHandler)

        self.mylog = logger

        self.doNotConnect = False
        self.requestStarted = datetime.now(tz=tz.tzlocal())

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

        self.hist_data_fetcher = None
        self.min_data = None

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
