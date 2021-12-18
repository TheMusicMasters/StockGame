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
api_key=os.getenv('ts_token_key')
ts.set_token(api_key)
pro = ts.pro_api()

st.header('中国A股股票交易预测系统 (更新至 2021年10月22日)')

intro_expander = st.expander(label='使用说明')
with intro_expander :
    st.subheader("**版权所有（copyright） : themusicmasters.official@gmail.com**")
    st.write("""
    - **风险警示 : 股市有风险，入市需谨慎。本系统仅提供参考，不提供购买和投资建议，请根据自身情况合理投资。**
    - **使用说明 : 本系统使用收盘价（CLOSE）和收盘价对十日均线偏差值（RMA10 = 100*(CLOSE - MA10)/MA10）作为主要参数，分三步完成选股，买股和卖股的一个交易流程。**
    - **选股标准 : 当某只股票的RMA10在某日收盘时大于（选股RMA10值）时，表示该股票的股价近期有大幅上涨，属于市场的强势股，触发信号标记到该只股票。**
    - **买入信号 : 带有触发信号标记的股票短期涨幅过大或者受市场大盘影响，自身会有回调的要求，这时当RMA10小于（买入RMA10值）且当日换手率大于（最小换手率）时触发买入信号。**
    - **卖出信号 : 根据市场的情绪，当获利超过（获利利润值）时触发卖出信号。**
    """)

st.sidebar.subheader('创建股票历史数据(前60天）')
#end_time = st.sidebar.date_input('End date',datetime.date.today())
today = date.today()
start = today - timedelta(days=60)
start_date = st.sidebar.date_input('Start date', start)
end_date = st.sidebar.date_input('End date', today)
sDate = str(start_date).replace('-','')
eDate = str(end_date).replace('-','')
tradingDays = []
if start_date < end_date:
    #st.sidebar.success(f'Start date: {start_date}\n\nEnd date: {end_date}')
    # get the trading days from tushare
    retries = 1
    success = False
    while not (success or retries > 3) :
        try:
            cal_df = pro.query('trade_cal', start_date=sDate, end_date=eDate)
            tradingDays = list(cal_df[cal_df.is_open == 1].cal_date.values)
            #st.sidebar.write(f'all trading days in selected period are {tradingDays}')
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

# 20210814 update the get_buyDf with tradingScan class
# todo check the datetime index for watch_df and buy_df
@st.cache
def tradingScan(daily_df, stockList, rma10_trigger, rma10_input):
    buy_df = pd.DataFrame()
    for n,stock in enumerate(stockList):
        #st.progress(n/len(stockList))
        stock_df = getStockDf(daily_df,stock)
        # check the max rma10
        # 20210816 v3 move to rma10_tradingScan()
        #trigger_signal, buy_signal, sell_signal = rma10_tradingScan(stock_df['rma10'], stock_df['close'])
        
        
        watch_df= stock_df[stock_df.rma10 > rma10_trigger]
        if watch_df.shape[0] :
            #print(f'{stock} was selected at tradingDate {watch_df.trade_date}')
            buy_df = buy_df.append(stock_df[stock_df.rma10 < rma10_input])
            #print(f'{stock} was bought at tradingDate {buy_df.trade_date}')                  
    return buy_df

# draw the k line
@st.cache
def get_stockDf_tushare(selected_stock,sDate,eDate):
    retries = 1
    maxRetries = 3
    
    success = False
    df = pd.DataFrame()
    while not (success or retries > maxRetries):
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
            wait = retries * 5
            print(f'Get k line data error! Waiting {wait} secs and re-trying...')
            sys.stdout.flush()
            time.sleep(wait)
            retries += 1
    return df

@st.cache
def getSummaryDf(buy_df,selected_tradeDate):
    #selected_tradeDate = 20210205
    selected_buyDf = buy_df[buy_df.trade_date == selected_tradeDate]
    # define the summary dataframe
    # row : stock ts_code
    # column : close value with trading date 
    summaryData = []
    stockIndex = []
    # loop stock 
    selectedStocks = selected_buyDf.ts_code.values
    for stock in selectedStocks:
        stock_df = getStockDf(daily_df,stock)
        stock_df.sort_values(by=['trade_date'],inplace=True)
        #print(dict(zip(stock_df.trade_date, stock_df.close)))
        summaryData.append(dict(zip(stock_df.trade_date, stock_df.close)))
        stockIndex.append(stock)
    summaryDf = pd.DataFrame(summaryData,index = stockIndex)
    # chunk the summary dataframe by trade_date
    i = list(summaryDf.columns).index(selected_tradeDate)
    subColumns = list(summaryDf.columns[i:])
    summaryDf = summaryDf[subColumns]
    return summaryDf

# functions used by customizing summaryDf
def red_font_highligt(series):
    highlight = 'color:white;background-color:blue;'
    #default = ''
    return [highlight for e in series]  

def bold_max_value_in_series(series):
    highlight = 'font-weight: bold;color:red;'
    default = ''
    return [highlight if e == series.max() else default for e in series] 

def bold_min_value_in_series(series):
    highlight = 'font-weight: bold;color:green'
    default = ''
    return [highlight if e == series.min() else default for e in series]

def bold_sell_value_in_series(series):
    buyPrice = float(list(series)[0])
    highlight = 'font-weight: bold;color:blue;background-color:yellow;'
    default = ''
    return [highlight if float(e) > buyPrice*1.1 else default for e in series] 

def get_rma10_trigger(rma10,close,triggerValue):
    signal   = []
    previous = -1.0
    for date,value in rma10.iteritems():
        if value > triggerValue:
            signal.append(close[date]*1.01)
        else:
            signal.append(np.nan)
        #previous = value
    return signal

def get_rma10_buy(rma10,close,buyValue):
    signal   = []
    previous = -1.0
    for date,value in rma10.iteritems():
        if value < buyValue:
            signal.append(close[date]*0.99)
        else:
            signal.append(np.nan)
        #previous = value
    return signal

# 20210816 new tradingScan for selling the stock if rma10 > 0
def rma10_tradingScan(rma10,close):
    buy_signal   = []
    sell_signal   = []
    trigger_signal   = []
    previous = -1.0
    trigger = False
    buy = False
    sell = True
    for date,value in rma10.iteritems():
        if value > 30 and trigger == False and sell == True:
            trigger_signal.append(close[date]*1.01)
            sell_signal.append(np.nan)
            buy_signal.append(np.nan)
            print(f'find tigger signal {date}')
            trigger = True
            buy = False
        elif trigger == True and value < -10 and buy == False:
            buy_signal.append(close[date]*0.99)
            trigger_signal.append(np.nan)
            sell_signal.append(np.nan)
            print(f'find buy signal {date} rma10 {value} price {close[date]}')
            buy = True
            sell = False
        elif value > 0 and buy == True and sell == False:
            sell_signal.append(close[date]*1.01)
            trigger_signal.append(np.nan)
            buy_signal.append(np.nan)
            print(f'find sell signal {date} rma10 {value} price {close[date]}')
            sell = True
            trigger = False
            buy == False
        else:
            trigger_signal.append(np.nan)
            sell_signal.append(np.nan)
            buy_signal.append(np.nan)

        #previous = value
    return trigger_signal, buy_signal, sell_signal


def rma10_tradingScan_profileRate(rma10,close,profileRate):
    buy_signal   = []
    sell_signal   = []
    trigger_signal   = []
    previous = -1.0
    trigger = False
    buy = False
    sell = True
    buy_price = 0
    for date,value in rma10.iteritems():
        if value > 30 and trigger == False and sell == True:
            trigger_signal.append(close[date]*1.01)
            sell_signal.append(np.nan)
            buy_signal.append(np.nan)
            print(f'find tigger signal {date}')
            trigger = True
            buy = False
        elif trigger == True and value < -10 and buy == False:
            buy_signal.append(close[date]*0.99)
            buy_price = close[date]
            trigger_signal.append(np.nan)
            sell_signal.append(np.nan)
            print(f'find buy signal {date} rma10 {value} price {close[date]}')
            buy = True
            sell = False
        #elif value > 0 and buy == True and sell == False:
        elif close[date]>buy_price*(1+ profileRate/100) and buy == True and sell == False:
            sell_signal.append(close[date]*1.01)
            trigger_signal.append(np.nan)
            buy_signal.append(np.nan)
            print(f'find sell signal {date} rma10 {value} price {close[date]}')
            sell = True
            trigger = False
            buy == False
            buy_price = 0
        else:
            trigger_signal.append(np.nan)
            sell_signal.append(np.nan)
            buy_signal.append(np.nan)

        #previous = value
    return trigger_signal, buy_signal, sell_signal


# def get_rma10_sell(rma10,close,buyValue):
#     signal   = []
#     previous = -1.0
#     for date,value in rma10.iteritems():
#         if value < buyValue:
#             signal.append(close[date]*0.99)
#         else:
#             signal.append(np.nan)
#         #previous = value
#     return signal

def plotKlines(daily_df,selected_stock):               
        #stock_stock_df = get_stockstock_df_tushare(selected_stock,sDate,eDate)
        stock_df = daily_df[daily_df.ts_code ==selected_stock]
        # two_cols = st.checkbox("2 columns?", True)
        # if two_cols:
        #     col1, col2 = st.beta_columns(2)
        # plot the RMA10 column
        stock_df['ma10'] = stock_df['close'].rolling(10).mean()
        # using loc method to avoid the SettingWithCopyWarning 
        stock_df.loc[:,'rma10'] = stock_df[['close','ma10']].apply(lambda x : (x['close'] - x['ma10'])*100/x['ma10'],axis = 1)
        stock_df.dropna()
        #stock_df = stock_df[::-1]
        stock_df['indexDate'] = stock_df['trade_date'].astype('str')
        stock_df['volume'] = stock_df['vol']
        stock_df.set_index('indexDate', inplace=True)
        stock_df.index = pd.to_datetime(stock_df.index)
        stock_df = stock_df.sort_index()
        
        #col1.line_chart(stock_df['close'])
        #st.line_chart(stock_df['rma10'])
        #ap0 = [ mpf.make_addplot(stock_df['rma10'],color='g',panel = 1),
        #       mpf.make_addplot(stock_df[stock_df['rma10']<-10],type='scatter',markersize=200,marker='^', panel = 1)]  # uses panel 0 by default
        #mpf.make_addplot(df['LowerB'],color='b'),  # uses panel 0 by default
        # add check with RMA10 for qfq dataframe
        
        # v2 feature
        # trigger_signal = get_rma10_trigger(stock_df['rma10'], stock_df['close'],rma10_trigger)
        # buy_signal = get_rma10_buy(stock_df['rma10'], stock_df['close'],rma10_buy)

        # apd = [ mpf.make_addplot(stock_df['rma10'],color='y',panel=2),
        #         mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'g'),
        #         mpf.make_addplot(buy_signal,type='scatter',markersize=50,marker='^',color = 'r')]
        
        #trigger_signal, buy_signal, sell_signal = rma10_tradingScan(stock_df['rma10'], stock_df['close'])
        trigger_signal, buy_signal, sell_signal = rma10_tradingScan_profileRate(stock_df['rma10'], stock_df['close'],10)
        apd = [mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'y')]
        
        if len([x for x in buy_signal if x > 0]) :
            apd = [mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'y'),
                    mpf.make_addplot(buy_signal,type='scatter',markersize=50,marker='^',color = 'r')]
            if len([x for x in sell_signal if x > 0]) :
                apd = [mpf.make_addplot(trigger_signal,type='scatter',markersize=50,marker='v',color = 'y'),
                    mpf.make_addplot(buy_signal,type='scatter',markersize=50,marker='^',color = 'r'),
                    mpf.make_addplot(sell_signal,type='scatter',markersize=50,marker='v',color = 'g')]
        #mpf.plot(stock_df,type='candle',mav=(5,10,20),volume=True, addplot=apd)

        for n,date in enumerate(stock_df['rma10'].index) :
            if not np.isnan(trigger_signal[n]) :
                st.write(f'{date} trigger signal found')
            elif not np.isnan(buy_signal[n]) :
                st.write(f'{date} buy stock with price {buy_signal[n]}')
            elif not np.isnan(sell_signal[n]) :
                st.write(f'{date} sell stock with price {sell_signal[n]}')
        
        st.pyplot(mpf.plot(stock_df,type='candle',mav=(5,10),volume=True, addplot=apd))


daily_df = build_dailyDf(tradingDays)

#if st.sidebar.button('Bulid DataFrame'):
if daily_df.shape[0]:
    stockList = np.unique(daily_df.ts_code.values)
    st.sidebar.success(f'数据加载成功！共 {len(tradingDays)} 个交易日， 共有{len(stockList)}只股票，共有{daily_df.shape[0]} 条股票交易信息。')
    # Selections 
    #st.subheader('Set your trading Scan Parameters')
    st.sidebar.subheader('设置你的个性化交易参数')
    #col1, col2,col3 = st.columns(3)
    rma10_trigger = st.sidebar.number_input('选股RMA10值', 10,100,30)
    rma10_buy = st.sidebar.number_input('买入RMA10值', -50,0,-10)
    rma10_sell = st.sidebar.number_input('卖出利润值', 0,30,10)
    hsl_input = st.sidebar.number_input('最小换手率',1,100,10)
    col4,col5,col6 = st.columns(3)
    
    # options to select subset of all stocks
    cyb_list = [x for x in stockList if x[:2]== '30']
    zxb_list = [x for x in stockList if x[:3] in ['002','003']]
    kcb_list = [x for x in stockList if x[:3] in ['688','689']]
    shb_list = [x for x in stockList if x[:2]== '60']
    szb_list = [x for x in stockList if x[:3] in ['000','001']]
    stockList_options = {'AllSTOCK':stockList,'CYB':cyb_list,'ZXB':zxb_list,'KCB':kcb_list,'SH':shb_list,'SZ':szb_list}
    selected_stockList = col4.selectbox('Select stockList',list(stockList_options.keys()),index = 2)
    # loop all stocks and scan the buy_df entries
    #buy_df = get_buyDf(daily_df,stockList_options[selected_stockList],rma_input)
    buy_df = tradingScan(daily_df,stockList_options[selected_stockList],rma10_trigger, rma10_buy)
    
    # todo validate buy_df dataframe
    
    # if st.button('validation of buy_df'):
    #     validate_buyDf(buy_df)
        #print(stock_df[stock_df.rma10 < -10])
    if buy_df.shape[0] :
        buy_expander = st.expander(label='显示所有交易')
        with buy_expander :
            st.table(buy_df)
        date_selection = list(np.unique(buy_df.trade_date.values))
        type_selection = ['All','Trigger','Buy','Sell','OnHold']
        #for date in date_selection:
        selected_date = col5.selectbox('Select the trading day', date_selection, index= len(date_selection) -1)
        selected_type = col6.selectbox('Select the trading type', type_selection, index = 0)
        
        st.subheader('Display buy-in summary table')
        st.write(f'Trading day {selected_date}, selected stocks are {list(buy_df[buy_df.trade_date == selected_date].ts_code.values)}')
        
        # v2 202010807 summaryDf
        summaryDf = getSummaryDf(buy_df,selected_date)
        # customize dataframe table
        #summaryDf.style.set_sticky(axis="index")
        subcol = []
        subcol.append(selected_date)
        summaryDf.style.apply(red_font_highligt, subset=subcol, axis=0)\
                .apply(bold_max_value_in_series, axis=1)\
                .apply(bold_min_value_in_series, axis=1)\
                .apply(bold_sell_value_in_series, axis=1)
        #st.dataframe(summaryDf.style.highlight_max(axis=1))
        st.table(summaryDf)
        
        
        st.subheader('Display k lines plot of selected stocks')
        display_all =st.checkbox('Display all selected stocks?',False)
        stock_selection = list(np.unique(summaryDf.index.values))
        
        if display_all:
            for stock in stock_selection :
                st.write(stock)
                plotKlines(daily_df,stock)
        else :
            selected_stock = st.selectbox('Select the stock code', stock_selection)
            plotKlines(daily_df,selected_stock)
            
    # v3 new feature 'user defined k line plot'
search_expander = st.expander(label='自定义查询')
with search_expander :
    col_text, col_button = st.columns(2)
    stock_code = col_text.text_input('输入你要查询的股票代码（格式 600375.SH）', '600375.SH')
    search =col_button.checkbox('查询',False)
    #search_button = col_button.button('查询')
    if search:
        st.write(stock_code)
        plotKlines(daily_df,stock_code)
        # Print trading history
        # buy stock and sell stock
        
        
        
            


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
