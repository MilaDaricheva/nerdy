from ib_insync import IB, Future
from hist_data import HistData


class HistDataFetcher:
    def onMinBarUpdate(self, bars, hasNewBar):
        # update 1min bars
        if hasNewBar:
            u_min_data = HistData(bars, self.mylog)
            self.min_data = u_min_data
            self.mylog.info("---------------------------")
            self.mylog.info("hist data")
            self.mylog.info(bars[-1])

    def fetchHistData(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Starting the connection for Hist Data")

        self.ib = IB()

        self.ib.connect('127.0.0.1', 7496, clientId=self.clientID)

        mesContract = Future('MES', '20210917', 'GLOBEX', 'MESU1', '5', 'USD')

        self.mylog.info("new reqHistoricalData...")

        self.min_bars = self.ib.reqHistoricalData(
            mesContract, endDateTime='', durationStr='2 D',
            barSizeSetting='1 min', whatToShow='MIDPOINT', useRTH=False,
            formatDate=1,
            keepUpToDate=True)

        self.mylog.info("---------------------------")
        self.mylog.info("process his data")

        self.min_data = HistData(self.min_bars, self.mylog)
        self.min_data.printLastN(4)

        self.min_bars.updateEvent += self.onMinBarUpdate

    def killFetcher(self):
        self.mylog.info("---------------------------")
        self.mylog.info("disconnect fetcher")
        self.ib.cancelHistoricalData(self.min_bars)
        self.mylog.info(self.clientID)
        self.ib.disconnect()

    def getMinData(self):
        return self.min_data

    def __init__(self, logger, clientID):
        self.mylog = logger
        self.clientID = clientID
        self.ib = None
        self.min_bars = None
        self.min_data = None
        self.mylog.info("---------------------------")
        self.mylog.info("Init fetcher")
        self.mylog.info(self.clientID)
        self.fetchHistData()
