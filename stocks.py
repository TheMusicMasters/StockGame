# author Zhen.Yan@cern.ch

class Stocks :
    def __init__(self, stockName, stockCode, stockTradingFlag, stockDate, stockPrice, stockAmount):
        self.stockName = stockName
        self.stockCode = stockCode
        self.stockTradingFlag = stockTradingFlag
        self.stockDate = stockDate
        self.stockPrice = stockPrice
        self.stockAmount = stockAmount
        self.stockValue = self.stockPrice * self.stockAmount
        #print(f'{self.stockTradingFlag} Stock {self.stockName} {self.stockCode}, {self.stockAmount} with price {self.stockPrice} at {self.stockDate}')
       
       
    def printSummary(self) : 
        print(f'Stock {self.stockName} {self.stockCode} amount {self.stockAmount} price {self.stockPrice} at {self.stockDate}, total value is {self.stockValue}')
     
    def updateValue(self) :
        self.stockValue = self.stockPrice * self.stockAmount
        