import pandas as pd
import numpy as np


class TradingConfig():
    """
    Author themusicmasters.official@gmail.com
    Twitter@themusicmaster9
    Class to create the tradingConfig from UI input
    RMA10(Relative price between CLOSE and MA10)
    HSL(Exchange rate)
    maxLoss (maximum loss percentage)
    maxGain (maximum gain percentage)
    PR(Profile rate)
    """
    # move to kwargs initialization
    # def __init__(self, df, **kw):
    #     self.RMA10 = kw.get('RMA10',10)
    def __init__(self, rma10_trigger,rma10_buy,rma10_sell, hsl, maxLoss, maxGain, maxHoldingDays, profileRate):
        self.rma10_trigger = rma10_trigger
        self.rma10_buy = rma10_buy
        self.rma10_sell = rma10_sell
        self.hsl = hsl
        self.maxLoss = maxLoss
        self.maxGain = maxGain
        self.maxHoldingDays = maxHoldingDays
        self.profileRate = profileRate
        
    def setProfileRate(self, newProfileRate):
        self.profileRate = newProfileRate
    
    def setMaxLoss(self, newMaxLoss):
        self.maxLoss = newMaxLoss
    
    def setMaxGain(self, newMaxGain):
        self.maxGain = newMaxGain
    
    def setHSL(self, newHSL):
        self.hsl = newHSL
    
    def setRMA10_trigger(self, newRma10_trigger):
        self.rma10_trigger = newRma10_trigger
        
    def setRMA10_buy(self, newRma10_buy):
        self.rma10_buy = newRma10_buy
        
    def setRMA10_sell(self, newRma10_sell):
        self.rma10_sell = newRma10_sell
        
    def setMaxHoldingDays(self,newMaxHoldingDays):
        self.maxHoldingDays = newMaxHoldingDays
        
    def printSummary(self):
        #return f'Configuration of tradingScan done. Rma10_trigger {self.rma10_trigger}, rma10_buy {self.rma10_buy}, profileRate {self.profileRate}, hsl {self.hsl},'
        return f'交易参数设置完成! 当RMA10值大于{self.rma10_trigger}时加入备选股票池，\
                        当RMA10小于{self.rma10_buy}且当天换手率大于{self.hsl}%时买入股票，\
                        当获利超过{self.profileRate}%时卖出股票。'

        
        