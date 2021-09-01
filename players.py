# author Zhen.Yan@cern.ch
import numpy as np
import pandas as pd
import glob
#from players import Players
from stocks import Stocks
# class to hold the player info
# 2021/08/09 new Players class, define the attibutes
# 2021/08/30 update with more methods 
# request the dailyData/ folder

class Players :
    def __init__(self, my_index, my_name, my_initial, my_startDate, my_endDate):
        self.name = my_name
        self.index = my_index
        self.startDate = my_startDate
        self.endDate = my_endDate
        #self.balance = my_initial
        self.capital = my_initial
        self.curStockValue = 0
        self.curCash = 0
        self.curBalance = my_initial
        self.onHoldStocks = []
        self.onHoldStocksList = []
        self.tradingHistory = []
        self.tradingDateHistory = []
        self.balanceHistory = []
        self.stockDf = pd.DataFrame()
    
    # initialize the stockDf from dailyData folder 
    def initializeStockDf(self):
        dataFolder = "dailyData/"
        # All files ending with _daily.csv
        dataList = glob.glob(f"{dataFolder}*daily.csv")
        daily_df = pd.DataFrame()
        for d in dataList:
            daily_df = daily_df.append(pd.read_csv(d,index_col=0))
        if daily_df.shape[0] > 0 :
            self.stockDf = daily_df
            print(f'initializeStockDf is successful!')
            return True
        else :
            print(f'initializeStockDf failed!')
            return False
    
    # get stockDf summary
    def stockDf_summary(self):
        if self.stockDf.shape[0] :
            print(f'Total entries : {self.stockDf.shape[0]}')
            stockList = list(np.unique(self.stockDf.ts_code))
            print(f'Total stocks : {len(stockList)}')
            tradingDate = list(np.unique(self.stockDf.trade_date))
            print(f'Total trading days : {len(tradingDate)}')
        else :
            print('No data was loaded!')
        
    # tradingScan class, return a list of daily stock information
    #def tradingScan(self) :
    
    # to do with database connection
    def saveRecord(self):
        print(f'Save current player info into database')
        
    def printSummary(self):
        if len(self.onHoldStocks) > 0 :
            print(f'player No.{self.index} {self.name} has {len(self.onHoldStocks)} stock(s)')
            for st in self.onHoldStocks :
                st.printSummary()
        else :
            print(f'player No.{self.index} {self.name} has no stock')
        print(f'Player No.{self.index} {self.name}, current balance {self.balance}, fund {self.fund}, stockValue {self.stockValue}')
        return f'Player No.{self.index} {self.name}, current balance {self.balance}, fund {self.fund}, stockValue {self.stockValue}'

    
    def printOnHoldStocks(self) :
        info = []
        if len(self.onHoldStocks) > 0 :
            for index,st in enumerate(self.onHoldStocks) :
                print(f'Index {index} stock {st.stockCode} available sell amount {st.stockAmount}')
                info.append(f'Index {index} stock {st.stockCode} available sell amount {st.stockAmount}')
        else :
            print(f'player No.{self.index} {self.name} has no stock')
            info.append(f'player No.{self.index} {self.name} has no stock')
        return info
            
    def buyStock(self, stock):
        if self.fund >= stock.stockValue :
            
            print(f'{self.name} {stock.stockTradingFlag} {stock.stockCode} with {stock.stockPrice} amount {stock.stockAmount}, total amount {stock.stockValue}')
            
            # balance remain the same
            self.fund -= stock.stockValue
            self.stockValue += stock.stockValue 
            
            # add new buyIn stock into onHoldStoc
            onHoldStocks = [st.stockCode for st in self.onHoldStocks]
            if stock.stockCode in onHoldStocks :
                for st in self.onHoldStocks :
                    # update st attibutes by adding stock info if stock already existed
                    if stock.stockCode == st.stockCode :
                        st.stockAmount += stock.stockAmount
                        st.stockValue += stock.stockValue
                        st.stockPrice = st.stockValue  / st.stockAmount
                        print(f'{st.stockAmount} {st.stockValue} {st.stockPrice}')
                        st.stockDate = stock.stockDate
            else :  # append new stock into onHoldStock
                self.onHoldStocks.append(stock)
            self.printSummary()
        else :
            print('Not enough fund, buyStock failed!')
    
    def sellStock(self, stockIndex, sellPrice, sellAmount):
        if stockIndex < len(self.onHoldStocks) and sellPrice > 0 and sellAmount <= self.onHoldStocks[stockIndex].stockAmount :
            self.onHoldStocks[stockIndex].stockTradingFlag = 'sell'
            print(f'{self.name} {self.onHoldStocks[stockIndex].stockTradingFlag} {self.onHoldStocks[stockIndex].stockCode} with {sellPrice} amount {sellAmount}, total amount {sellPrice * sellAmount}')
            
            self.fund += sellPrice * sellAmount
            # update the onHoldStock list
            if sellAmount == self.onHoldStocks[stockIndex].stockAmount :
                self.onHoldStocks = self.onHoldStocks[0:stockIndex] + self.onHoldStocks[stockIndex+1 :]
            else :    
                self.onHoldStocks[stockIndex].stockAmount -= sellAmount
                self.onHoldStocks[stockIndex].updateValue()
            self.stockValue = 0
            for st in self.onHoldStocks :
                #print(f'{self.name} currently has {st.stockName} amount {st.stockAmount}')
                self.stockValue += st.stockValue
            # update the balance
            self.balance = self.fund + self.stockValue
            self.printSummary()
            
        else :
            print('No engout amount, sellStock failed!')
        
 