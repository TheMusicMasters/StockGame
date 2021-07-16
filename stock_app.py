#import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import time
from datetime import datetime
from tradingScan import TradingScan
st.set_page_config(layout='wide')
st.set_option('deprecation.showPyplotGlobalUse', False)

st.write("""
# My Stock App

Watching the price of my stock         
         
""")


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

# load local dataframe
stock = 'sh.600375'
#datafile = 'https://cernbox.cern.ch/index.php/s/ipUEu9vlriWW0ef'
datafile = f"{stock}_2021-06-25.csv"
df = pd.read_csv(datafile)

st.write(df)

#st.slider('dateIndex', min_value=0, max_value=10)
my_slider_val = st.sidebar.slider('dateIndex', 1, df.shape[0])
st.write(my_slider_val)
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

# draw the k line

df['indexDate'] = df['date']
df.set_index('indexDate', inplace=True)
df.index = pd.to_datetime(df.index)
fig = mpf.plot(df,type='candle',mav=(5,10,20),volume=True)
st.pyplot(fig)


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
