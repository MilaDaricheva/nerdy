#from ta.utils import dropna
from ib_insync import IB, Future, util
from hist_data_fetcher import HistDataFetcher
from hr_data_fetcher import HRDataFetcher
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
            self.ib.connect('127.0.0.1', 7497, clientId=1)

    def setUpHistData(self):
        if not self.hist_data_fetcher and not self.deadZone():
            self.mylog.info("---------------------------")
            self.mylog.info("setUpHistData + deadZone")
            self.mylog.info(self.deadZone())
            self.mylog.info(self.clientID)
            self.hist_data_fetcher = HistDataFetcher(self.mylog, self.clientID)

    def setUpHRData(self):
        if not self.hr_data_fetcher and not self.deadZone():
            self.mylog.info("---------------------------")
            self.mylog.info("setUpHRData + deadZone")
            self.mylog.info(self.deadZone())
            self.mylog.info(self.clientID)
            self.hr_data_fetcher = HRDataFetcher(self.mylog, self.clientID)

    def setUpData(self):
        self.mylog.info("---------------------------")
        self.mylog.info("setUpData")

        self.setUpHistData()
        self.setUpHRData()

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
            self.oBucket.emptyPosObject()
        if trade.order.action == 'SELL' and not self.ib.positions():
            # long closed
            self.mylog.info("long closed")
            self.oBucket.cancelAll()
            self.oBucket.emptyPosObject()

        # if trade.order.action == 'BUY' and self.ib.positions():
            # scale out of short happened
        #    if self.ib.positions()[0].position == -self.oBucket.scale1Size:
        #        self.mylog.info("scale out of 2d short happened")
            # move stops tighter
        #        self.mylog.info("move stops lmpPrice1 + 10")
        #        self.oBucket.adjustBraket(self.oBucket.rememberVPL - 23, self.oBucket.rememberVPL + 10)

        #    if self.ib.positions()[0].position == -(self.oBucket.scale1Size + self.oBucket.scale2Size):
        #        self.mylog.info("scale out of 3d short happened")
            # move stops tighter
        #        self.mylog.info("move stops (lmpPrice2 + lmpPrice3)/2")
        #        self.oBucket.adjustBraket(self.oBucket.rememberVPL - 23, self.oBucket.beStop)

        # if trade.order.action == 'SELL' and self.ib.positions():
            # scale out of long happened
        #    if self.ib.positions()[0].position == self.oBucket.scale1Size:
        #        self.mylog.info("scale out of 2d long happened")
            # move stops tighter
        #        self.mylog.info("move stops lmpPrice1 - 10")
        #        self.oBucket.adjustBraket(self.oBucket.rememberVPL + 23, self.oBucket.rememberVPL - 10)
        #    if self.ib.positions()[0].position == self.oBucket.scale1Size + self.oBucket.scale2Size:
        #        self.mylog.info("scale out of 3d long happened")
        #        # move stops tighter
        #        self.mylog.info("move stops (lmpPrice2 + lmpPrice3)/2")
        #        self.oBucket.adjustBraket(self.oBucket.rememberVPL + 23, self.oBucket.beStop)

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
            self.mylog.info("Error Code 162 - wth?")
            self.ib.disconnect()
            self.doNotConnect = True
        if (errorCode == 2105 or errorCode == 1100) and self.hist_data_fetcher:
            self.mylog.info("Hist data nah nah")
            self.hist_data_fetcher.killFetcher()
            self.hist_data_fetcher = None
            self.hr_data_fetcher.killFetcher()
            self.hr_data_fetcher = None
            self.clientID = self.clientID + 1
        if (errorCode == 2106 or errorCode == 1101 or errorCode == 1102) and not self.hist_data_fetcher and timeGap:
            self.mylog.info("Hist data seems ok")
            self.requestStarted = datetime.now(tz=tz.tzlocal())
            util.schedule(open_time, self.setUpHistData)
            util.schedule(open_time, self.setUpHRData)

    def onConnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connected Event")
        self.setUpData()

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
        close_time_from = datetime(now_time.year, now_time.month, now_time.day, 16, 50, 0, 0, tz.tzlocal())
        close_time_to = datetime(now_time.year, now_time.month, now_time.day, 16, 59, 0, 0, tz.tzlocal())

        if now_time < close_time_to and now_time > close_time_from:
            return True
        else:
            return False

    def timeIsOk(self):
        now_time = datetime.now(tz=tz.tzlocal())
        eod_time = datetime(now_time.year, now_time.month, now_time.day, 16, 50, 0, 0, tz.tzlocal())
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

            timeGap = datetime.now(tz=tz.tzlocal()) - self.requestStarted >= timedelta(minutes=5)

            if self.timeIsOk() and not self.deadZone():
                if not (self.hist_data_fetcher or self.hr_data_fetcher):
                    if timeGap:
                        self.mylog.info("---------------------------")
                        self.mylog.info("No fetcher, create one")
                        self.requestStarted = datetime.now(tz=tz.tzlocal())
                        self.setUpHistData()
                        self.setUpHRData()
                else:
                    self.min_data = self.hist_data_fetcher.getMinData()
                    self.hr_data = self.hr_data_fetcher.getHRData()

                    cuttentBarTime = bars[-1].time.astimezone(tz.tzutc())
                    nowTime = datetime.now(tz=tz.tzutc())

                    histBarTime = self.min_data.timeCreated
                    hrBarTime = self.hr_data.timeCreated

                    # self.mylog.info("self.min_data.timeCreated")
                    # self.mylog.info(histBarTime)

                    twSec = timedelta(seconds=20)
                    twoMin = timedelta(minutes=2)
                    twoHr = timedelta(hours=2)

                    rtDataOk = nowTime - twSec <= cuttentBarTime
                    histDataOk = nowTime - twoMin <= histBarTime
                    hrDataOk = nowTime - twoHr <= hrBarTime

                    if histDataOk and rtDataOk and hrDataOk:
                        #self.mylog.info("all data ok")
                        # self.mylog.info(nowTime)
                        rtd = RealTimeData(bars, self.min_data, self.hr_data, self.vp_levels, self.mylog)
                        sm = StrategyManagement(bars, self.min_data, self.hr_data, self.vp_levels, self.mylog)
                        om = OrderManagement(self.ib, self.contract, sm, self.oBucket, rtd, self.vpTouches, self.mylog)
                        om.goDoBusiness()
                    else:
                        if timeGap and not (histDataOk or hrDataOk):
                            self.mylog.info("---------------------------")
                            self.mylog.info("Hist or HR Data not OK, kill fetcher, UTC Time")
                            self.mylog.info(nowTime)
                            self.mylog.info(timeGap)
                            if self.hist_data_fetcher:
                                self.hist_data_fetcher.killFetcher()
                                self.hist_data_fetcher = None
                                self.clientID = self.clientID + 1
                            if self.hr_data_fetcher:
                                self.hr_data_fetcher.killFetcher()
                                self.hr_data_fetcher = None
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
        num_vp = 55
        sVP = 4249.63

        for i in range(num_vp):
            nextVP = round(sVP+14.955*i, 2)
            self.vp_levels.append(nextVP)
        self.mylog.info("---------------------------")
        self.mylog.info("VP levels")
        self.mylog.info(self.vp_levels[-1])

        # set IB
        self.mylog.info("---------------------------")
        self.mylog.info("Starting the connection")

        self.hist_data_fetcher = None
        self.min_data = None

        self.hr_data_fetcher = None
        self.hr_data = None

        self.clientID = 2

        self.ib = IB()

        self.ib.connect('127.0.0.1', 7497, clientId=1)

        self.contract = Future('MES', '20211217', 'GLOBEX', 'MESZ1', '5', 'USD')
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
