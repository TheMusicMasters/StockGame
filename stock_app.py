import matplotlib.pyplot as plt
import mplfinance as mpf
import streamlit as st
#import yfinance as yf
import akshare as ak
import pandas as pd
import numpy as np
import time, os, sys
import tushare as ts
from datetime import datetime, date, timedelta
from tradingScan import TradingScan

st.set_page_config(layout='wide')
st.set_option('deprecation.showPyplotGlobalUse', False)

# tushare api token
ts.set_token('5d2fe4ac143088a808f16d07757b4c21c55d25832ad57cd7f98b0188')
pro = ts.pro_api()

st.write("""
# Stock Scan App (China Stock Market)
**RMA10** is the key parameter I use to scan the market
""")

st.sidebar.write('Build up the daily dataframe')
#end_time = st.sidebar.date_input('End date',datetime.date.today())
today = date.today()
start = today - timedelta(days=23)
start_date = st.sidebar.date_input('Start date', start)
end_date = st.sidebar.date_input('End date', today)
sDate = str(start_date).replace('-','')
eDate = str(end_date).replace('-','')
tradingDays = []
if start_date < end_date:
    st.sidebar.success(f'Start date: {start_date}\n\nEnd date: {end_date}')
    # get the trading days from tushare
    retries = 1
    success = False
    while not success:
        try:
            cal_df = pro.query('trade_cal', start_date=sDate, end_date=eDate)
            tradingDays = list(cal_df[cal_df.is_open == 1].cal_date.values)
            st.write(f'all trading days in selected period are {tradingDays}')
            success = True
        except Exception as e:
            wait = retries * 5;
            print(f'Get trading calendar error! Waiting {wait} secs and re-trying...')
            sys.stdout.flush()
            time.sleep(wait)
            retries += 1
        
else:
    st.sidebar.error('Error: End date must fall after start date.')

# build the daily dataframe
def valid_tradingDate(df,trading_day):
    tradingDate = list(np.unique(df.trade_date))[0]
    print(f'trading date in data {tradingDate} and input {trading_day}')
    if str(tradingDate) == str(trading_day) :
        return True
    else :
        return False

# 
@st.cache
def build_dailyDf(tradingDays):
    daily_df = pd.DataFrame()
    for trading_day in tradingDays:
        outputName = f'dailyData/{trading_day}_daily.csv'
        # add check the date to the
        if not os.path.isfile(outputName):
            print(f"Downloading {trading_day} daily data" )
            retries = 1
            success = False
            while not success:
                try:
                    one_df = pro.daily(trade_date= trading_day)
                    success = True
                except Exception as e:
                    wait = retries * 5;
                    print(f'Error! Waiting {wait} secs and re-trying...')
                    sys.stdout.flush()
                    time.sleep(wait)
                    retries += 1
            #one_df = pro.daily(trade_date= trading_day)
            #time.sleep(5)
            if valid_tradingDate(one_df,trading_day):
                one_df.to_csv(outputName)
                print(f"Saved {trading_day} daily data to {outputName}")
                daily_df = daily_df.append(pd.read_csv(outputName,index_col=0))
            else :
                print(f"Wrong {trading_day} daily data to {outputName}")
        else :
            # check the trade_date matach with file name
            if valid_tradingDate(pd.read_csv(outputName), trading_day):
                daily_df = daily_df.append(pd.read_csv(outputName,index_col=0))
            else :
                print(f"Wrong {trading_day} daily data to {outputName}")
    return daily_df

def getStockDf(daily_df,stock):
    stock_df = daily_df[daily_df.ts_code == stock]
    stock_df.sort_values(by=['trade_date'])
    # create the new column for tradingScan
    stock_df['ma10'] = stock_df['close'].rolling(10).mean()
    # using loc method to avoid the SettingWithCopyWarning 
    stock_df.loc[:,'rma10'] = stock_df[['close','ma10']].apply(lambda x : (x['close'] - x['ma10'])*100/x['ma10'],axis = 1)
    stock_df.dropna()
    return stock_df

@st.cache
def get_buyDf(daily_df,stockList,rma_input):
    buy_df = pd.DataFrame()
    for n,stock in enumerate(stockList):
        #st.progress(n/len(stockList))
        stock_df = getStockDf(daily_df,stock)
        buy_df = buy_df.append(stock_df[stock_df.rma10 < rma_input])
    return buy_df

# draw the k line
@st.cache
def get_stockDf_tushare(selected_stock,sDate,eDate):
    retries = 1
    success = False
    df = pd.DataFrame()
    while not success:
        try:
            df = ts.pro_bar(ts_code=selected_stock, start_date=sDate, end_date=eDate, ma=[5,10], adj = 'qfq')
            df = df[::-1]
            df['indexDate'] = df['trade_date']
            df['volume'] = df['vol']
            df.set_index('indexDate', inplace=True)
            df.index = pd.to_datetime(df.index)
            print(f'Get {selected_stock} k line data successfully')
            success = True
        except Exception as e:
            wait = retries * 5;
            print(f'Get k line data error! Waiting {wait} secs and re-trying...')
            sys.stdout.flush()
            time.sleep(wait)
            retries += 1
    return df

daily_df = build_dailyDf(tradingDays)
#if st.sidebar.button('Bulid DataFrame'):
if daily_df.shape[0]:
    st.sidebar.success(f'Build daily dataframe successfully! Total {len(tradingDays)} trading days, and total {daily_df.shape[0]} entries')
    # Selections 
    st.sidebar.write('Your trading Scan Parameters')
    
    rma_input = st.sidebar.number_input('RMA10 value', -10)
    hsl_input = st.sidebar.number_input('MHSL10 value(to be added)', 10)
    
    stockList = np.unique(daily_df.ts_code.values)
    # options to select subset of all stocks
    cyb_list = [x for x in stockList if x[:2]== '30']
    zxb_list = [x for x in stockList if x[:3] in ['002','003']]
    kcb_list = [x for x in stockList if x[:3] in ['688','689']]
    shb_list = [x for x in stockList if x[:2]== '60']
    szb_list = [x for x in stockList if x[:3] in ['000','001']]
    stockList_options = {'AllSTOCK':stockList,'CYB':cyb_list,'ZXB':zxb_list,'KCB':kcb_list,'SH':shb_list,'SZ':szb_list}
    selected_stockList = st.sidebar.selectbox('Select stockList',list(stockList_options.keys()),index = 1)
    # loop all stocks and scan the buy_df entries
    buy_df = get_buyDf(daily_df,stockList_options[selected_stockList],rma_input)
        #print(stock_df[stock_df.rma10 < -10])
    if buy_df.shape[0] :
        date_selection = list(np.unique(buy_df.trade_date.values))
        #for date in date_selection:
        selected_date = st.selectbox('Select the trading day', date_selection, index= len(date_selection) -1)
        st.write(f'Trading day {selected_date}, selected stocks are {list(buy_df[buy_df.trade_date == selected_date].ts_code.values)}')
        
        stock_selection = list(np.unique(buy_df.ts_code.values))
        selected_stock = st.selectbox('Select the stock code', stock_selection)
                   
        stock_df = get_stockDf_tushare(selected_stock,sDate,eDate)
        
        # add check with RMA10 for qfq dataframe
        st.pyplot(mpf.plot(stock_df,type='candle',mav=(5,10,20),volume=True))
        st.write(stock_df)
            


# # Get hot rates for 600375
# today = datetime.today()
# d1 = today.strftime("%Y%m%d")
# #print("d1 = ", d1)
# stock_wc_hot_rank_df = ak.stock_wc_hot_rank(date=d1)
# st.write(stock_wc_hot_rank_df[stock_wc_hot_rank_df.股票代码 == '600375'])
# workflows
# Get the full stock list from tushares
# Input text file as the filter string



# if st.button('股吧热度前20'):
#     stock_wc_hot_rank_df = ak.stock_wc_hot_rank(date="20210709")
#     st.write(stock_wc_hot_rank_df.head(20))
# else:
#     # st.write('股吧热度')
# tickerSymbol = '600375.SS'

# tickerData = yf.Ticker(tickerSymbol)

# today = time.strftime("%Y-%m-%d")

# # SetuptickerDf = tickerData.history(period='1d',start='2021-06-01',end=today)
# tickerDf = tickerData.history(period='max')
# st.write(tickerDf.head())
# # sidebar
# st.sidebar.header('Selection')
# selected_year = st.sidebar.selectbox('Year',list(reversed(tickerDf.index)))


# st.line_chart(tickerDf.Volume)

# st.line_chart(tickerDf.Close)

# # load local dataframe
# stock = 'sh.600375'
# #datafile = 'https://cernbox.cern.ch/index.php/s/ipUEu9vlriWW0ef'
# datafile = f"{stock}_2021-06-25.csv"
# df = pd.read_csv(datafile)

# switch to online data (test in juypter notebook)


#st.slider('dateIndex', min_value=0, max_value=10)
# my_slider_val = st.sidebar.slider('dateIndex', 1, df.shape[0],15,1)
# st.write(my_slider_val)
# st.line_chart(df.high[my_slider_val:])
# start_date = st.sidebar.slider("StartDate", value=datetime(2020, 1, 1), format="YYYY-MM-DD")
# st.write("Start time:", start_date)

# end_date = st.sidebar.slider("EndDate", value=datetime(2021, 1, 1), format="YYYY-MM-DD")
# st.write("End time:", end_date)

# #current = st.sidebar.slider('dateIndex', 1, df.shape[0])
# start_index = df[df.date==str(start_date)[:10]].index[0]
# st.write("Start Index:", start_index)

# end_index = df[df.date==str(end_date)[:10]].index[0]
# st.write("End Index:", end_index)
################################################################
# get stock name from sidebar drop list

# download data from baostock

# st.header('Stock dataframe')
# st.write(df)


# # adding tradingScan

# model1 = TradingScan(df, RMA10 = 10, AHSL10 = 5, PR = 10)

# st.write(model1.scan())

# # progress_bar = st.progress(0)
# # status_text = st.empty()
# # chart = st.line_chart(np.random.randn(10, 2))

# # for i in range(100):
# #     # Update progress bar.
# #     progress_bar.progress(i + 1)

# #     new_rows = np.random.randn(10, 2)

# #     # Update status text.
# #     status_text.text(
# #         'The latest random number is: %s' % new_rows[-1, 1])

# #     # Append data to the chart.
# #     chart.add_rows(new_rows)

# #     # Pretend we're doing some computation that takes time.
# #     time.sleep(0.1)

# # status_text.text('Done!')
# # st.balloons()

# import tushare as ts
# import os,sys
# # setup tushare token and get the pro interface
# ts.set_token('5d2fe4ac143088a808f16d07757b4c21c55d25832ad57cd7f98b0188')
# pro = ts.pro_api()
# daily_df = pd.DataFrame()
# trading_day = '20210630'
# st.write(f"Downloading {trading_day} daily data" )
# daily_df = pro.daily(trade_date= trading_day)
# st.write(daily_df)
