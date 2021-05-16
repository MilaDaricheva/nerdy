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

import nest_asyncio

nest_asyncio.apply()

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.INFO)


class AlgoVP:
    def onErrorEvent(self, reqId, errorCode, errorString, contract):
        logging.info("---------------------------")
        logging.info("My error handler here")
        logging.info(errorString)

    def onMinBarUpdate(self, bars, hasNewBar):
        # update 1min bars
        if hasNewBar:
            u_min_data = HistData(bars)
            self.min_data = u_min_data
            #logging.info('Updated 1min')
            # self.min_data.printLastN(4)

    def onRTBarUpdate(self, bars, hasNewBar):
        # new real time 5sec bar
        if hasNewBar:
            #logging.info("Time Game")
            # UTC
            cuttentBarTime = bars[-1].time.astimezone(tz.tzutc())
            nowTime = datetime.now(tz=tz.tzutc())
            histBarTime = self.min_data.timeCreated

            twSec = timedelta(seconds=20)
            twoMin = timedelta(minutes=2)

            rtDataOk = nowTime - twSec <= cuttentBarTime
            histDataOk = nowTime - twoMin <= histBarTime

            logging.info("---------------------------")
            logging.info("Time Data")
            logging.info(cuttentBarTime)
            logging.info(nowTime - twSec)
            logging.info(rtDataOk)
            logging.info(nowTime - twoMin)
            logging.info(histDataOk)
            logging.info(bars[-1])
            logging.info("---------------------------")

            if histDataOk:
                if rtDataOk:
                    self.min_data.printLastN(4)

                    rtd = RealTimeData(bars, self.min_data, self.vp_levels)

                    sm = StrategyManagement(bars, self.min_data, self.vp_levels)

                    om = OrderManagement(self.ib, self.contract, sm, self.oBucket, rtd, self.vpTouches)

                    om.goDoBusiness()

                    logging.info("bucket")
                    logging.info(self.oBucket.firstLong)
                    logging.info(self.oBucket.firstShort)

            else:
                # request Hist Data Again
                logging.info("---------------------------")
                logging.info("Renew Hist Data Subscription")
                # self.ib.cancelHistoricalData(self.min_bars)
                #self.min_bars = None
                # self.min_bars = self.ib.reqHistoricalData(
                #    self.contract, endDateTime='', durationStr='2 D',
                #    barSizeSetting='1 min', whatToShow='MIDPOINT', useRTH=False,
                #    formatDate=1,
                #    keepUpToDate=True)

                #self.min_data = HistData(self.min_bars)
                self.min_data.printLastN(4)

                #self.min_bars.updateEvent += self.onMinBarUpdate

    def __init__(self):
        self.ib = IB()
        self.ib.connect('127.0.0.1', 7496, clientId=1)
        self.contract = Future('MES', '20210618', 'GLOBEX', 'MESM1', '5', 'USD')

        self.min_bars = self.ib.reqHistoricalData(
            self.contract, endDateTime='', durationStr='2 D',
            barSizeSetting='1 min', whatToShow='MIDPOINT', useRTH=False,
            formatDate=1,
            keepUpToDate=True)

        self.min_data = HistData(self.min_bars)
        self.min_data.printLastN(4)

        self.min_bars.updateEvent += self.onMinBarUpdate

        # main vp levels
        self.vp_levels = []
        num_vp = 50
        sVP = 3880.51

        for i in range(num_vp):
            nextVP = round(sVP+13.065*i, 2)
            self.vp_levels.append(nextVP)

        # logging.info(vp_levels)

        self.oBucket = OrdersBucket(self.ib, self.contract)
        self.vpTouches = VpTouches()

        rt_bars = self.ib.reqRealTimeBars(self.contract, 5, 'MIDPOINT', False)
        rt_bars.updateEvent += self.onRTBarUpdate

        self.ib.errorEvent += self.onErrorEvent

        self.ib.run()


startAlgo = AlgoVP()
