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

#import nest_asyncio

# nest_asyncio.apply()

#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class AlgoVP:
    def setUpData(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connected")

        self.contract = Future('MES', '20210618', 'GLOBEX', 'MESM1', '5', 'USD')
        self.ib.qualifyContracts(self.contract)

        self.min_bars = self.ib.reqHistoricalData(
            self.contract, endDateTime='', durationStr='2 D',
            barSizeSetting='1 min', whatToShow='MIDPOINT', useRTH=False,
            formatDate=1,
            keepUpToDate=True)

        self.min_data = HistData(self.min_bars, self.mylog)
        self.min_data.printLastN(4)

        self.min_bars.updateEvent += self.onMinBarUpdate

        self.oBucket = OrdersBucket(self.ib, self.contract, self.mylog)
        self.vpTouches = VpTouches(self.mylog)

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
                self.mylog.info("scale out of short happened")
                # cancel 3d scale, move stops be
                self.mylog.info("cancel 3d short")
                self.oBucket.cancel3d(-1)
                self.oBucket.moveStops(self.oBucket.beStop)
        if trade.order.action == 'SELL' and self.ib.positions():
            # scale out of long happened
            if self.ib.positions()[0].position == self.oBucket.scale1Size:
                self.mylog.info("scale out of long happened")
                # cancel 3d scale, move stops be
                self.mylog.info("cancel 3d long")
                self.oBucket.cancel3d(1)
                self.oBucket.moveStops(self.oBucket.beStop)

    def onErrorEvent(self, reqId, errorCode, errorString, contract):
        self.mylog.info("---------------------------")
        self.mylog.info("My error handler here")
        self.mylog.info(errorCode)
        self.mylog.info(errorString)

    def onConnectedEvent(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Connected Event")
        self.setUpData()

    def onMinBarUpdate(self, bars, hasNewBar):
        # update 1min bars
        if hasNewBar:
            u_min_data = HistData(bars, self.mylog)
            self.min_data = u_min_data

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

            # self.mylog.info(nowTime - twSec)
            # self.mylog.info(rtDataOk)
            # self.mylog.info(nowTime - twoMin)
            # self.mylog.info(histDataOk)
            # self.mylog.info(bars[-1])
            # self.mylog.info("---------------------------")

            if histDataOk:
                if rtDataOk:
                    # self.mylog.info("---------------------------")
                    # self.mylog.info("Time Data")
                    # self.mylog.info(cuttentBarTime)
                    # self.min_data.printLastN(4)

                    rtd = RealTimeData(bars, self.min_data, self.vp_levels, self.mylog)

                    sm = StrategyManagement(bars, self.min_data, self.vp_levels, self.mylog)

                    om = OrderManagement(self.ib, self.contract, sm, self.oBucket, rtd, self.vpTouches, self.mylog)

                    om.goDoBusiness()

                    # self.mylog.info("bucket")
                    # self.mylog.info(self.oBucket.firstLong)
                    # self.mylog.info(self.oBucket.firstShort)

            else:
                # Disconnect/Connect
                self.mylog.info("---------------------------")
                self.mylog.info("Disconnect/Connect")
                self.ib.disconnect()
                self.ib.sleep(60)
                self.ib.connect('127.0.0.1', 7496, clientId=1)

    def __init__(self):
        # set logger
        logger = logging.getLogger('my_app')
        logger.setLevel(logging.INFO)

        logHandler = handlers.RotatingFileHandler('app.log', maxBytes=3*1024*1024, backupCount=2)
        logHandler.setLevel(logging.INFO)
        logger.addHandler(logHandler)

        self.mylog = logger

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

        if self.ib.isConnected():
            self.setUpData()

        self.ib.connectedEvent += self.onConnectedEvent

        self.ib.errorEvent += self.onErrorEvent

        self.ib.execDetailsEvent += self.onPositionChange

        self.ib.run()


startAlgo = AlgoVP()
