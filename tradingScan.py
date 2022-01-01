import pandas as pd
import numpy as np


class TradingScan():
    """
    Author themusicmasters.official@gmail.com
    Twitter@themusicmaster9
    Class to create the trading model by using tradingConfig
    RMA10(Relative price between CLOSE and MA10)
    AHSL10(Average days HSL)
    TMA10(Trend of MA10 +/-)
    PR(Profile rate)
    Input pandas DataFrame of one stock
    Ouput trading entries matching the trading model
    """
    
    def __init__(self, df, **kw):
        self.DF = df
        self.RMA10 = kw.get('RMA10',10)
        self.AHSL10 = kw.get('AHSL10',10)
        self.PR = kw.get('PR',10)
        self.TMA10 = kw.get('TMA10',1)
        self.Code = self.getStockCode()
        
    def getStockCode(self):
        # get stockName, make sure only one stock data in this dataframe
        print(f'Stock code in the dataframe is {np.unique(self.DF.code)}')
        return np.unique(self.DF.code)[0]
    
    def scan(self):
        # create the columns used by scanning
        nIndex = self.DF.shape[0]  # number of the entries
        buy_df = self.DF[self.DF['ma10'].astype(float)*(1-self.RMA10/100.) > self.DF['close'].astype(float)]
        # 2nd fliter with exchange rate (alternative solution by using amount10 for tushare data)
        buy_df = buy_df[buy_df['ta10'].astype(float) > self.AHSL10]
        buy_index = list(buy_df.index)
        tradings = []
        if buy_index != []:
            print(buy_index)
            currentDate = buy_index[0]+1
            for i in buy_index:
                # set pointer to df index
                if i < currentDate : continue
                buyPrice = self.DF.iloc[i].close
                buyDate = self.DF.iloc[i].date
                print(f'Buy stock {self.Code} with price {buyPrice} at {buyDate}')
                tradings.append(f'Buy stock {self.Code} with price {buyPrice} at {buyDate}\n')
                # searching the next entries to find the selling price and date
                for n in range(i,nIndex):
                    sellPrice = float(self.DF.iloc[n].close)
                    sellDate = self.DF.iloc[n].date
                    nDays = n - i
                    # check the sell conditions
                    if sellPrice > buyPrice *(1+self.PR/100.) :
                        profile = 100*(sellPrice - buyPrice)/buyPrice
                        currentDate = n
                        nDays = n - i
                        print(f'Sell stock {self.Code} with price {sellPrice} at {sellDate}, profile {profile}% after {nDays} days')
                        tradings.append(f'Sell stock {self.Code} with price {sellPrice} at {sellDate}, profile {profile}% after {nDays} days\n')
                        break
        return tradings                
                
                