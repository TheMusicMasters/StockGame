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
from tradingConfig import TradingConfig
from stockData import StockData
from players import Players

st.set_page_config(layout='wide')
st.set_option('deprecation.showPyplotGlobalUse', False)

ts.set_token('5d2fe4ac143088a808f16d07757b4c21c55d25832ad57cd7f98b0188')
pro = ts.pro_api()

st.header('中国A股股票预测系统 (版本4.0)')

intro_expander = st.expander(label='使用说明')
with intro_expander :
    st.subheader("**版权所有（copyright） : themusicmasters.official@gmail.com**")
    st.write("""
    - **风险警示 : 股市有风险，入市需谨慎。本系统仅提供参考，不提供购买和投资建议，请根据自身情况合理投资。**
    - **使用说明 : 本系统使用收盘价（CLOSE）和收盘价对十日均线偏差值（RMA10 = 100*(CLOSE - MA10)/MA10）作为主要参数，分三步完成选股，买股和卖股的一个交易流程。**
    - **选股标准 : 当某只股票的RMA10在某日收盘时大于（选股RMA10值）时，表示该股票的股价近期有大幅上涨，属于市场的强势股，触发信号标记到该只股票。**
    - **买入信号 : 带有触发信号标记的股票短期涨幅过大或者受市场大盘影响，自身会有回调的要求，这时当RMA10小于（买入RMA10值）时触发买入信号。当日换手率HSL以及股吧热度可以作为辅助选股标准适当参考。**
    - **卖出信号 : 根据市场的情绪，当获利超过（获利利润值）时触发卖出信号。默认为盈利10%时卖出。**
    """)
    
@st.cache
def getChineseNameDf():
    chineseNameDf = pro.query('stock_basic', exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,exchange,list_date')
    return chineseNameDf
    
# build daily stockData with cache
@st.cache(allow_output_mutation=True)
def build_dailyDf(inputType, sDate, eDate):
    sd = StockData(inputType, sDate, eDate)
    daily_df = sd.getStockDf()
    stockList = sd.getAllStockNames()
    tradingDays = sd.getAllTradingDates()
    summaryInfo = sd.printSummary()
    return daily_df, stockList, tradingDays, summaryInfo
# filter daily_df to player_df
@st.cache
def filtered_stockDf(daily_df,selected_stockList):
    player_df = daily_df[daily_df.ts_code.isin(selected_stockList)]
    return player_df

@st.cache(allow_output_mutation=True)
def scanMarket(player):
    return player.tradingScan()
    
# v4 new layout
with st.container():
    #data_col, config_col, player_col = st.columns(3) 
    data_col, config_col = st.columns(2)  #move player_col to game app
    data_col.subheader('创建股票历史数据(默认使用前70天,约50个交易日）')
    #end_time = st.sidebar.date_input('End date',datetime.date.today())
    today = date.today()
    # check utcnow to make sure to download today's new stock data after the market closing at 17h UTC+8 time zone
    if datetime.utcnow().hour < 9 :
        #data_col.info('当日数据需要等到市场交易结束后才能使用')
        today = today - timedelta(days=1)
    start = today - timedelta(days=70)
    start_date = data_col.date_input('Start date', start)
    end_date = data_col.date_input('End date', today)
    sDate = str(start_date).replace('-','')
    eDate = str(end_date).replace('-','')
    inputType = data_col.radio("Choose the input type",('CSV', 'SQL'),0,)
    
    # bulid dataDf with cache
    daily_df, stockList, tradingDays, summaryInfo = build_dailyDf(inputType, sDate, eDate)
    # daily_df = sd.getStockDf()
    # stockList = sd.getAllStockNames()
    # tradingDays = sd.getAllTradingDates()

#if st.sidebar.button('Bulid DataFrame'):
# only active the following trading scan if loading stockDf success and trading period greater than 30 days
    if daily_df.shape[0] and len(tradingDays) > 30:
        data_col.success(summaryInfo)
        # market selections (new update, use chineseNameDf from tushare API)
        # options to select subset of all stocks, v4 adding Beijing list
        chineseNameDf = getChineseNameDf()
        marketList = list(np.unique(chineseNameDf.market.values))
        marketList.append('全部A股')
        
        # setup config_col
        #st.subheader('Set your trading Scan Parameters')
        config_col.subheader('设置你的个性化交易参数')
        with config_col:
            with config_col.form('Form1'):
                rma10_trigger = st.number_input('选股RMA10值', 10,100,30)
                rma10_buy = st.number_input('买入RMA10值', -50,0,-10)
                profileRate = st.number_input('卖出盈利比例',1,100,10)
                selected_marketList = st.selectbox('选择证券交易市场',marketList,index = 3)
                submitted = st.form_submit_button('重新扫描历史数据')
        if submitted :
            selected_stockList = []
            if selected_marketList == '全部A股':
                selected_stockList = list(chineseNameDf.ts_code.values)
            else :
                selected_stockList = list(chineseNameDf[chineseNameDf.market == selected_marketList].ts_code.values)
            # create filtered dataframe
            player_df = filtered_stockDf(daily_df,selected_stockList)
            # create default tradingConfig
            tc = TradingConfig(rma10_trigger,rma10_buy,0,10,30,30,30,profileRate)    
            config_col.success(tc.printSummary())
        # rma10_trigger = config_col.number_input('选股RMA10值', 10,100,30)
        # rma10_buy = config_col.number_input('买入RMA10值', -50,0,-10)
        # profileRate = config_col.number_input('卖出盈利比例',1,100,10)
        # config_expander = config_col.expander(label='高级参数')
        # with config_expander :
        #     hsl = config_expander.number_input('最小换手率',1,100,10)
        #     rma10_sell = config_expander.number_input('卖出利润值', 0,30,10)
        #     maxLoss = config_expander.number_input('最大亏损比例',1,100,10)
        #     maxGain = config_expander.number_input('最大盈利比例',1,100,10)
        #     maxHoldingDays = config_expander.number_input('最长持有时间',1,100,100)
        
        # player columns contents move to game app
        # player_col.subheader('设置你的游戏角色参数')
        
        # player_name = player_col.text_input('输入你的游戏角色名称','玩家001')
        # player_fund = player_col.number_input('输入你的初始资金',100000)
        # player_mode = player_col.selectbox('选择你的游戏模式',['自动','手动'],index = 0)
        
        
        # cyb_list = [x for x in stockList if x[:2]== '30']
        # zxb_list = [x for x in stockList if x[:3] in ['002','003']]
        # kcb_list = [x for x in stockList if x[:3] in ['688','689']]
        # shb_list = [x for x in stockList if x[:2]== '60']
        # szb_list = [x for x in stockList if x[:3] in ['000','001']]
        # bj_list =  [x for x in stockList if x[-3:] == '.BJ']
        # stockList_options = {'所有市场':stockList,'创业板':cyb_list,'中小板':zxb_list,'科创板':kcb_list,'上海':shb_list,'深圳':szb_list,'北京':bj_list}
        
        # filter the stockDf by selected_stockList
        
            #info_col, button_col = st.columns([4,1])
            # create player object
            player_name = 'PredictionBot'
            player_fund = 1000000
            player = Players(1,player_name,player_fund,player_df,tc)
            
            #st.info()
            #info_col.info(player.printPlayerInfo())
            
            # cache scan function
            summaryDf, watchingList, onHoldList = scanMarket(player)
            summaryDf = summaryDf.sort_values(by=['buyDate'])
            
            #start_button = button_col.button('开始扫描')
            # main output container for trading scan
            if not summaryDf.empty :
                #if player_mode == '自动' :
                buy_expander = st.expander(label='显示所有交易')
                with buy_expander :
                    nBuy = summaryDf.shape[0]
                    nSell = summaryDf[summaryDf.onHoldFlag == False].shape[0]
                    nHold = summaryDf[summaryDf.onHoldFlag == True].shape[0]
                    summaryDf.loc[:,'profileRate'] = summaryDf[['buyPrice','sellPrice']].apply(lambda x : (x['sellPrice'] - x['buyPrice'])*100/x['buyPrice'],axis = 1)
                    
                    st.info(f'符合买入条件的股票共有{nBuy}，成功获利{nSell}，目前持有{nHold}, 综合盈利{summaryDf.profileRate.sum()}%')
                    
                    # print trading details
                    for row in summaryDf.itertuples(index=False):
                        nDays = (row.sellDate - row.buyDate).days
                        chName = chineseNameDf[chineseNameDf.ts_code == row.ts_code].name.values[0]          
                        if row.onHoldFlag == False :
                            st.success(f'{row.buyDate.date()}推荐买入{chName}{row.ts_code}，买入价格{row.buyPrice}, 买入当天换手率{row.buyHSL},持有天数{nDays}，于{row.sellDate.date()}价格{row.sellPrice}卖出, 获利比例为{row.profileRate}')
                        else :
                            st.warning(f'{row.buyDate.date()}推荐买入{chName}{row.ts_code}，买入价格{row.buyPrice}, 持有天数{nDays},截止到{row.sellDate.date()}，收盘价{row.sellPrice}，获利比例为{row.profileRate}')

                    #st.download_button(label="Download data as CSV", data=summaryDf, file_name='large_df.csv',mime='text/csv')
                    # 显示扫描结果
                    # 交易成功百分比，当前盈利状况
                    #st.table(summaryDf)
                # hsl_expander = st.expander(label='换手率>15%的所有交易')
                # with hsl_expander :
                #     summaryDfHsl = summaryDf[summaryDf.buyHSL > 15]
                #     nBuy = summaryDfHsl.shape[0]
                #     nSell = summaryDfHsl[summaryDfHsl.onHoldFlag == False].shape[0]
                #     nHold = summaryDfHsl[summaryDf.onHoldFlag == True].shape[0]
                #     st.info(f'符合买入条件的股票共有{nBuy}，成功获利{nSell}，目前持有{nHold}，综合盈利{summaryDfHsl.profileRate.sum()}%')
                #     # 显示扫描结果
                #     # 交易成功百分比，当前盈利状况
                #     st.table(summaryDfHsl)
                
                #watching_col, recom_col, success_col = st.columns(3)
                
                watching_expander = st.expander(label='备选股票池')
                if len(watchingList) > 0 :
                    with watching_expander:
                        links = []
                        for stock,nTrigger in watchingList :
                            chineseName = chineseNameDf[chineseNameDf.ts_code == stock].name.values[0]
                            dcName = f'{stock[-2:]}{stock[:6]}'
                            link = f'[{chineseName}({stock})](http://quote.eastmoney.com/{dcName}.html)'
                            links.append(link)
                        watching_expander.write(' '.join(links))
                        #display_all_watching =watching_expander.checkbox('显示所有备选股票K线图',False)
                        #if display_all_watching:
                        for stock,nTrigger in watchingList :
                            dcName = f'{stock[-2:]}{stock[:6]}'
                            chineseName = chineseNameDf[chineseNameDf.ts_code == stock].name.values[0]
                            watching_expander.write(f'[{chineseName}({stock})](http://quote.eastmoney.com/{dcName}.html)')
                            player.drawKlines(stock)
                        # else :
                        #     selected_stock = watching_expander.selectbox('选择你想查看的备选股票', [stock for stock,nTrigger in watchingList])
                        #     dcName = f'{selected_stock[-2:]}{selected_stock[:6]}'
                        #     watching_expander.write(f'东方财富股吧链接[{selected_stock}](http://quote.eastmoney.com/{dcName}.html)')  
                        #     player.drawKlines(selected_stock)
                else :
                    watching_expander.write('没有找到符合条件的股票')
                            
                
                recom_expander = st.expander(label='推荐股票池')
                if len(onHoldList) > 0 :
                    with recom_expander:
                        links = []
                        for stock,nTrigger in onHoldList :
                            chineseName = chineseNameDf[chineseNameDf.ts_code == stock].name.values[0]
                            dcName = f'{stock[-2:]}{stock[:6]}'
                            link = f'[{chineseName}({stock})](http://quote.eastmoney.com/{dcName}.html)'
                            links.append(link)
                        recom_expander.write(' '.join(links))
                        # display_all_onHold =recom_expander.checkbox('显示所有推荐股票K线图?',False)
                        # if display_all_onHold:
                        for stock,nTrigger in onHoldList:
                            chineseName = chineseNameDf[chineseNameDf.ts_code == stock].name.values[0]
                            dcName = f'{stock[-2:]}{stock[:6]}'
                            recom_expander.write(f'{chineseName}({stock})](http://quote.eastmoney.com/{dcName}.html)')
                            player.drawKlines(stock)
                        # else :
                        #     selected_stock = recom_expander.selectbox('选择你想查看的推荐股票', [stock for stock,nTrigger in onHoldList])
                        #     dcName = f'{selected_stock[-2:]}{selected_stock[:6]}'
                        #     recom_expander.write(f'东方财富股吧链接[{selected_stock}](http://quote.eastmoney.com/{dcName}.html)')     
                        #     player.drawKlines(selected_stock)
                else :
                    recom_expander.write('没有找到符合条件的股票')
                    
                success_expander = st.expander(label='成功交易记录')
                successList = list(summaryDf[summaryDf.onHoldFlag == False].ts_code.values)
                
                if len(successList) > 0 :
                    with success_expander:
                        links = []
                        for stock in successList :
                            chineseName = chineseNameDf[chineseNameDf.ts_code == stock].name.values[0]
                            dcName = f'{stock[-2:]}{stock[:6]}'
                            link = f'[{chineseName}({stock})](http://quote.eastmoney.com/{dcName}.html)'
                            links.append(link)
                        # success_expander.write(' '.join(links))
                        # display_all_success =success_expander.checkbox('显示所有成功交易股票K线图?',False)
                        #if display_all_success:
                        for stock in successList:
                            chineseName = chineseNameDf[chineseNameDf.ts_code == stock].name.values[0]
                            dcName = f'{stock[-2:]}{stock[:6]}'
                            success_expander.write(f'{chineseName}({stock})](http://quote.eastmoney.com/{dcName}.html)')
                            player.drawKlines(stock)
                        # else :
                        #     selected_stock = success_expander.selectbox('选择你想查看的成功交易股票', list(summaryDf[summaryDf.onHoldFlag == False].ts_code.values))
                        #     dcName = f'{selected_stock[-2:]}{selected_stock[:6]}'
                        #     success_expander.write(f'东方财富股吧链接[{selected_stock}](http://quote.eastmoney.com/{dcName}.html)')     
                        #     player.drawKlines(selected_stock)        
                else :
                    success_expander.write('没有找到符合条件的股票')        
                
            # st.subheader('Display k lines plot of selected stocks')
            # display_all =st.checkbox('Display all selected stocks?',True)
            # stock_selection = np.unique([trade['ts_code'] for trade in onHoldList])
            
            # if display_all:
            #     for stock in stock_selection :
            #         dcName = f'{stock[-2:]}{stock[:6]}'
            #         st.write(f'东方财富链接[{stock}](http://quote.eastmoney.com/{dcName}.html)')
            #         player.drawKlines(stock)
            # else :
            #     selected_stock = st.selectbox('Select the stock code', stock_selection)
            #     player.drawKlines(selected_stock)
                
            
        
        
    


# create player object
    