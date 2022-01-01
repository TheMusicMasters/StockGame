# Author themusicmasters.official@gmail.com
# Twitter@themusicmaster9
import numpy as np
import pandas as pd
import glob
#from players import Players
from stocks import Stocks
from stockData import StockData
from tradingConfig import TradingConfig
from tradingScan import TradingScan
import matplotlib.pyplot as plt
import mplfinance as mpf
import streamlit as st
import akshare as ak

class Players :
    """
    Author themusicmasters.official@gmail.com
    Twitter@themusicmaster9
    Class to create the player profile by using stockData tradingScan and tradingConfig
    Input stockData
    Main Algorithm : tradingScan
    Ouput trading entries matching the trading model
    Todo : 
        improve printPlayerInfo()
        
    """
    def __init__(self, my_index, my_name, my_initial, stockDf, my_tradingConfig):
        self.name = my_name
        self.index = my_index
        # self.startDate = my_startDate
        # self.endDate = my_endDate
        #self.balance = my_initial
        self.capital = my_initial
        self.curStockValue = 0
        self.curCash = 0
        self.curBalance = my_initial
        self.tradingHistory = []
        self.tradingDateHistory = []
        self.balanceHistory = []
        self.stockDf = stockDf
        self.tradingConfig = my_tradingConfig
        self.summaryDf = pd.DataFrame()
        self.watchingList = []
        self.onHoldStocksList = []
        self.timeLine = {} 
    
    # initialize the stockDf from dailyData folder
    
    # get stockDf summary
    def printPlayerInfo(self):
        return f'{self.name} 你好，你的初始资金为{self.capital}，你的当前余额为{self.curBalance}，你当前持有股票为{self.onHoldStocksList}。'
    
    # BJ stock no return HSL    
    def getHSL(self,stockCode,sDate,eDate):
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stockCode, start_date=sDate, end_date=eDate,adjust="qfq")
        #print(f'stock {stockCode} startDate {sDate} endDate {eDate} has HSL {stock_zh_a_hist_df.换手率.values}')
        if stock_zh_a_hist_df.empty :
            return 0
        else :
            return stock_zh_a_hist_df.换手率.values[0]

    def tradingScan(self):
        stockList = list(np.unique(self.stockDf.ts_code))
        mergedList = []
        watchingList = []
        onHoldList = []
        
        for m,stock in enumerate(stockList):
            print(stock)
            stock_df, tradingEntries, trigger_signal, buy_signal, sell_signal = self.tradingScan_single(stock)
            if trigger_signal == [] : continue
            mergedList.extend(tradingEntries)
            
            if sum(np.isnan(trigger_signal))!=len(trigger_signal) and sum(np.isnan(sell_signal))==len(sell_signal):
                if sum(np.isnan(buy_signal))==len(buy_signal):
                    watchingList.append((stock,len(trigger_signal) - sum(np.isnan(trigger_signal))))
                else :
                    onHoldList.append((stock,len(trigger_signal) - sum(np.isnan(trigger_signal))))
                    
        summaryDf = pd.DataFrame(mergedList,columns = ['ts_code','trigger_date','nTrigger','buyDate','buyPrice','buyRMA10','buyHSL','sellDate','sellPrice','sellRMA10','onHoldFlag'])
        self.summaryDf = summaryDf
        return summaryDf,watchingList,onHoldList
    
    def tradingScan_single(self, stock):
        buy_signal   = []
        sell_signal   = []
        trigger_signal   = []
        previous = -1.0
        trigger = False
        nTrigger = False
        buy = False
        sell = True
        buy_price = 0
        onHold = False
        
        # config output summary columns
        # format [ts_code,trigger_date,nTrigger,buyDate,buyPrice,buyRMA10,buyHSL,sellDate,sellPrice,sellRMA10,onHoldFlag]
        tradeEntries = []
        #watchingList = False  # trigger = true, buy = false, sell = false
        
        stock_df = self.stockDf[self.stockDf.ts_code == stock]
        stock_df.sort_values(by=['trade_date'])
        # df.set_index('indexDate', inplace=True)
        # df.index = pd.to_datetime(df.index)
        # create the new column for tradingScan
        stock_df['ma10'] = stock_df['close'].rolling(10).mean()
        # using loc method to avoid the SettingWithCopyWarning 
        stock_df.loc[:,'rma10'] = stock_df[['close','ma10']].apply(lambda x : (x['close'] - x['ma10'])*100/x['ma10'],axis = 1)
        stock_df.dropna()
        stock_df['indexDate'] = stock_df['trade_date'].astype('str')
        stock_df['volume'] = stock_df['vol']
        stock_df.set_index('indexDate', inplace=True)
        stock_df.index = pd.to_datetime(stock_df.index)
        stock_df = stock_df.sort_index()
        
        # check trigger single beforehand, return df and empty
        trigger_threshold = stock_df[stock_df['rma10']>30].shape[0]
        if trigger_threshold < 1 : 
            print(f'No trigger signal was found, skip stock {stock}!')
            return stock_df, tradeEntries, trigger_signal, buy_signal, sell_signal
        print(f'Trigger signal was found, start to scan stock {stock}!')
        fTriggerDate = stock_df.iloc[0].trade_date # init frist trigger signal date
        for date,value in stock_df.rma10.iteritems():
            if value > self.tradingConfig.rma10_trigger and trigger == False and sell == True:
                trigger_signal.append(stock_df.close[date]*1.01)
                sell_signal.append(np.nan)
                buy_signal.append(np.nan)
                trigger = True
                nTrigger = 1 # record frist trigger signal counter
                fTriggerDate = date # record frist trigger signal date
                buy = False
            elif trigger == True and buy == False:
                if value < self.tradingConfig.rma10_buy :
                    # adding HSL check
                    hsl = self.getHSL(stock[:6],date,date)
                    buy_signal.append(stock_df.close[date]*0.99)
                    buy_price = stock_df.close[date]
                    trigger_signal.append(np.nan)
                    sell_signal.append(np.nan)
                    print(f'{stock} find buy signal {date} rma10 {value} price {stock_df.close[date]}')
                    buy = True
                    sell = False
                    # fill the output summary list
                    tradeEntry = []
                    tradeEntry.append(stock)
                    tradeEntry.append(fTriggerDate)
                    tradeEntry.append(nTrigger)
                    tradeEntry.append(date)
                    tradeEntry.append(stock_df.close[date])
                    tradeEntry.append(value)
                    tradeEntry.append(hsl)                                        
                    
                elif value > self.tradingConfig.rma10_trigger :
                    buy_signal.append(np.nan)
                    buy_price = 0
                    trigger_signal.append(stock_df.close[date]*1.01)
                    nTrigger += 1
                    sell_signal.append(np.nan)
                    #print(f'find trigger signal {date} rma10 {value} price {stock_df.close[date]}')
                    buy = False
                    trigger = True
                    
                else :
                    trigger_signal.append(np.nan)
                    sell_signal.append(np.nan)
                    buy_signal.append(np.nan)
            # add the check for stock_df.high[date] > buy_price*1.08 
            elif (buy == True) and (sell == False):
                if stock_df.close[date] > buy_price*(1+ self.tradingConfig.profileRate/100) :
                    sell_signal.append(stock_df.close[date]*1.01)
                    trigger_signal.append(np.nan)
                    buy_signal.append(np.nan)
                    print(f'{stock} find sell signal {date} rma10 {value} price {stock_df.close[date]}')
                    sell = True
                    trigger = False
                    buy == False
                    buy_price = 0
                    tradeEntry.append(date)
                    tradeEntry.append(stock_df.close[date])
                    tradeEntry.append(value)
                    onHold = False
                    tradeEntry.append(onHold)
                    tradeEntries.append(tradeEntry)
                    
                # if reaching the last trading date, sell the stock anyway
                elif date == stock_df.index[-1] :
                    trigger_signal.append(np.nan)
                    sell_signal.append(np.nan)
                    buy_signal.append(np.nan)
                    tradeEntry.append(date)
                    tradeEntry.append(stock_df.close[date])
                    tradeEntry.append(value)
                    onHold = True
                    buy == False
                    sell == False
                    tradeEntry.append(onHold)
                    tradeEntries.append(tradeEntry)
                    print(f'{stock} not find sell signal. Sell the stock at latest trading day {date} rma10 {value} price {stock_df.close[date]}')
                else :
                    trigger_signal.append(np.nan)
                    sell_signal.append(np.nan)
                    buy_signal.append(np.nan)

            else:
                trigger_signal.append(np.nan)
                sell_signal.append(np.nan)
                buy_signal.append(np.nan)

        return stock_df, tradeEntries, trigger_signal, buy_signal, sell_signal
    
    
    def drawKlines(self, selected_stock):
        
        stock_df, tradeEntries, trigger_signal, buy_signal, sell_signal = self.tradingScan_single(selected_stock)
        apd = [mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'y')]
        
        if len([x for x in buy_signal if x > 0]) :
            apd = [mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'y'),
                    mpf.make_addplot(buy_signal,type='scatter',markersize=50,marker='^',color = 'r')]
            if len([x for x in sell_signal if x > 0]) :
                apd = [mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'y'),
                    mpf.make_addplot(buy_signal,type='scatter',markersize=50,marker='^',color = 'r'),
                    mpf.make_addplot(sell_signal,type='scatter',markersize=50,marker='v',color = 'g')]
        #mpf.plot(stock_df,type='candle',mav=(5,10,20),volume=True, addplot=apd)

        for n,date in enumerate(stock_df.index) :
            # if not np.isnan(trigger_signal[n]) :
            #     st.write(f'{date} find {selected_stock} trigger signal')
            if not np.isnan(buy_signal[n]) :
                st.write(f'股票 {selected_stock} 在 {date} 触发买入信号，买入价格 {buy_signal[n]}')
            elif not np.isnan(sell_signal[n]) :
                st.write(f'股票 {selected_stock} 在 {date} 触发卖出信号，卖出价格 {sell_signal[n]}')
        
        st.pyplot(mpf.plot(stock_df,type='candle',mav=(5,10),volume=True, addplot=apd))
    
    # # to do with database connection
    # def saveRecord(self):
    #     print(f'Save current player info into database')
        
    # def printSummary(self):
    #     if len(self.onHoldStocks) > 0 :
    #         print(f'player No.{self.index} {self.name} has {len(self.onHoldStocks)} stock(s)')
    #         for st in self.onHoldStocks :
    #             st.printSummary()
    #     else :
    #         print(f'player No.{self.index} {self.name} has no stock')
    #     print(f'Player No.{self.index} {self.name}, current balance {self.balance}, fund {self.fund}, stockValue {self.stockValue}')
    #     return f'Player No.{self.index} {self.name}, current balance {self.balance}, fund {self.fund}, stockValue {self.stockValue}'

    
    # def printOnHoldStocks(self) :
    #     info = []
    #     if len(self.onHoldStocks) > 0 :
    #         for index,st in enumerate(self.onHoldStocks) :
    #             print(f'Index {index} stock {st.stockCode} available sell amount {st.stockAmount}')
    #             info.append(f'Index {index} stock {st.stockCode} available sell amount {st.stockAmount}')
    #     else :
    #         print(f'player No.{self.index} {self.name} has no stock')
    #         info.append(f'player No.{self.index} {self.name} has no stock')
    #     return info
            
    # def buyStock(self, stock):
    #     if self.fund >= stock.stockValue :
            
    #         print(f'{self.name} {stock.stockTradingFlag} {stock.stockCode} with {stock.stockPrice} amount {stock.stockAmount}, total amount {stock.stockValue}')
            
    #         # balance remain the same
    #         self.fund -= stock.stockValue
    #         self.stockValue += stock.stockValue 
            
    #         # add new buyIn stock into onHoldStoc
    #         onHoldStocks = [st.stockCode for st in self.onHoldStocks]
    #         if stock.stockCode in onHoldStocks :
    #             for st in self.onHoldStocks :
    #                 # update st attibutes by adding stock info if stock already existed
    #                 if stock.stockCode == st.stockCode :
    #                     st.stockAmount += stock.stockAmount
    #                     st.stockValue += stock.stockValue
    #                     st.stockPrice = st.stockValue  / st.stockAmount
    #                     print(f'{st.stockAmount} {st.stockValue} {st.stockPrice}')
    #                     st.stockDate = stock.stockDate
    #         else :  # append new stock into onHoldStock
    #             self.onHoldStocks.append(stock)
    #         self.printSummary()
    #     else :
    #         print('Not enough fund, buyStock failed!')
    
    # def sellStock(self, stockIndex, sellPrice, sellAmount):
    #     if stockIndex < len(self.onHoldStocks) and sellPrice > 0 and sellAmount <= self.onHoldStocks[stockIndex].stockAmount :
    #         self.onHoldStocks[stockIndex].stockTradingFlag = 'sell'
    #         print(f'{self.name} {self.onHoldStocks[stockIndex].stockTradingFlag} {self.onHoldStocks[stockIndex].stockCode} with {sellPrice} amount {sellAmount}, total amount {sellPrice * sellAmount}')
            
    #         self.fund += sellPrice * sellAmount
    #         # update the onHoldStock list
    #         if sellAmount == self.onHoldStocks[stockIndex].stockAmount :
    #             self.onHoldStocks = self.onHoldStocks[0:stockIndex] + self.onHoldStocks[stockIndex+1 :]
    #         else :    
    #             self.onHoldStocks[stockIndex].stockAmount -= sellAmount
    #             self.onHoldStocks[stockIndex].updateValue()
    #         self.stockValue = 0
    #         for st in self.onHoldStocks :
    #             #print(f'{self.name} currently has {st.stockName} amount {st.stockAmount}')
    #             self.stockValue += st.stockValue
    #         # update the balance
    #         self.balance = self.fund + self.stockValue
    #         self.printSummary()
            
    #     else :
    #         print('No engout amount, sellStock failed!')
        
 