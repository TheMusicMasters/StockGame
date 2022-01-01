import numpy as np
import pandas as pd
import glob, sys, os, time
import tushare as ts

class StockData :
    """
    Author themusicmasters.official@gmail.com
    Twitter@themusicmaster9
    Class to create the dailyDf
        - inputType (CSV or SQL)
        - startDate (yyyymmdd)
        - endDate (yyyymmdd)
    Ouput dailyDf and summary
    """
    def __init__(self, inputType, startDate, endDate):
        self.inputType = inputType
        self.startDate = startDate
        self.endDate = endDate
        self.stockDf = pd.DataFrame()
        self.stockList = []
        self.tradingDateList = []
        #print(f'{self.stockTradingFlag} Stock {self.stockName} {self.stockCode}, {self.stockAmount} with price {self.stockPrice} at {self.stockDate}')
       
    def valid_tradingDate(self, df, trading_day):
        tradingDate = list(np.unique(df.trade_date))[0]
        print(f'trading date in data {tradingDate} and input {trading_day}')
        if str(tradingDate) == str(trading_day) :
            return True
        else :
            return False
    
    def getStockDf(self) :
        
        ts.set_token('5d2fe4ac143088a808f16d07757b4c21c55d25832ad57cd7f98b0188')
        pro = ts.pro_api()
        tradingDays = []
        if self.startDate < self.endDate :
            print(f'Start date: {self.startDate}\n\nEnd date: {self.endDate}')
            # get the trading days from tushare
            retries = 1
            success = False
            while not (success or retries > 3) :
                try:
                    cal_df = pro.query('trade_cal', start_date=self.startDate, end_date=self.endDate)
                    tradingDays = list(cal_df[cal_df.is_open == 1].cal_date.values)
                    print(f'All trading days in selected period are {tradingDays}')
                    success = True
                except Exception as e:
                    wait = retries * 5;
                    print(f'Get trading calendar error! Waiting {wait} secs and re-trying...')
                    sys.stdout.flush()
                    time.sleep(wait)
                    retries += 1
                
        else:
            print('Error: End date must fall after start date.')
            
        daily_df = pd.DataFrame()
        for trading_day in tradingDays:
            outputName = f'dailyData/{trading_day}_daily.csv'
            # add check the date to the
            if not os.path.isfile(outputName):
                print(f"Downloading {trading_day} daily data" )
                retries = 1
                maxRetries = 3
                success = False
                while not (success or retries > maxRetries):
                    try:
                        one_df = pro.daily(trade_date= trading_day)
                        success = True
                    except Exception as e:
                        wait = retries * 5
                        print(f'Error! Waiting {wait} secs and re-trying...')
                        sys.stdout.flush()
                        time.sleep(wait)
                        retries += 1
                #one_df = pro.daily(trade_date= trading_day)
                #time.sleep(5)
                if self.valid_tradingDate(one_df,trading_day):
                    one_df.to_csv(outputName)
                    print(f"Saved {trading_day} daily data to {outputName}")
                    daily_df = daily_df.append(pd.read_csv(outputName,index_col=0))
                else :
                    print(f"Wrong {trading_day} daily data to {outputName}")
            else :
                # check the trade_date matach with file name
                if self.valid_tradingDate(pd.read_csv(outputName), trading_day):
                    daily_df = daily_df.append(pd.read_csv(outputName,index_col=0))
                else :
                    print(f"Wrong {trading_day} daily data to {outputName}")
        self.stockDf = daily_df
        self.stockList = self.getAllStockNames()
        self.tradingDateList = self.getAllTradingDates()
        return daily_df
    
    def getAllTradingDates(self) :
        tradingDates = list(np.unique(self.stockDf.trade_date))
        return tradingDates
        
    def getAllStockNames(self) :
        stockNames = list(np.unique(self.stockDf.ts_code))
        return stockNames
       
    def printSummary(self) : 
        return f'{self.inputType}数据加载成功！共 {len(self.tradingDateList)} 个交易日， 共有{len(self.stockList)}只股票，共有{self.stockDf.shape[0]} 条股票交易信息。'
        