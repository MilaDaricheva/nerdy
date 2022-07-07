from ib_insync import IB, Future
from hr_data import HRData
from fut_info import FutInfo


class HRDataFetcher:
    def onHRBarUpdate(self, bars, hasNewBar):
        # update 1hr bars
        if hasNewBar:
            u_hr_data = HRData(bars, self.mylog)
            self.hr_data = u_hr_data
            self.mylog.info("---------------------------")
            self.mylog.info("hist HR data")
            self.mylog.info(bars[-1])

    def fetchHRData(self):
        self.mylog.info("---------------------------")
        self.mylog.info("Starting the connection for HR Hist Data")

        self.ib = IB()

        self.ib.connect('127.0.0.1', FutInfo.myPort(), clientId=self.clientID)

        mesContract = Future('MES', FutInfo.expir(), 'GLOBEX', FutInfo.symb(), '5', 'USD')

        self.mylog.info("new reqHistoricalData...")

        self.hr_bars = self.ib.reqHistoricalData(
            mesContract, endDateTime='', durationStr='4 D',
            barSizeSetting='5 mins', whatToShow='MIDPOINT', useRTH=False,
            formatDate=1,
            keepUpToDate=True)

        if self.hr_bars:
            self.mylog.info("---------------------------")
            self.mylog.info("process his data")

            self.hr_data = HRData(self.hr_bars, self.mylog)
            self.hr_data.printLastN(4)

            self.hr_bars.updateEvent += self.onHRBarUpdate
        else:
            self.mylog.info("No HR bars returned.")

    def killFetcher(self):
        if self.ib.isConnected():
            self.mylog.info("---------------------------")
            self.mylog.info("disconnect HR fetcher")
            self.ib.cancelHistoricalData(self.hr_bars)
            self.mylog.info(self.clientID)
            self.ib.disconnect()

    def getHRData(self):
        return self.hr_data

    def __init__(self, logger, clientID):
        self.mylog = logger
        self.clientID = 30*clientID
        self.ib = None
        self.hr_bars = None
        self.hr_data = None
        self.mylog.info("---------------------------")
        self.mylog.info("Init HR fetcher")
        self.mylog.info(self.clientID)
        self.fetchHRData()
