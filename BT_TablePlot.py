#!/usr/bin/env python
# coding: utf-8

import numpy as np
import pandas as pd
import math
import os
import matplotlib.pyplot as plt
import dataframe_image as dfi

def generate_dir(name):
    if not os.path.isdir(name):
        os.mkdir(name)
    os.chdir(name)

bt1 = pd.read_csv('Pool_0.3% EWMA/split_long/width_list_long/Backtest_result.csv')
bt2 = pd.read_csv('Pool_0.3% EWMA/split_long/width_list_short/Backtest_result.csv')
bt3 = pd.read_csv('Pool_0.3% EWMA/split_short/width_list_long/Backtest_result.csv')
bt4 = pd.read_csv('Pool_0.3% EWMA/split_short/width_list_short/Backtest_result.csv')
bt_list = [bt1,bt2,bt3,bt4]


# # Tables

for bt in bt_list:
    bt['Diff with B&H(no gasfee)'] = bt['Total_val'] + bt['reallowcation fee'] - bt['B&H']
    bt['Diff with B&H'] = bt['Total_val'] - bt['B&H']
    bt['Diff with B&H(no hedge)'] = bt['Uni_val'] - bt['B&H']
    
    bt['Cum_return(B&H)'] = (bt['B&H'] - 500000)/500000
    for i in range(1,len(bt['Cum_return(B&H)'])):
        bt['Cum_return(B&H)'][i] += bt['Cum_return(B&H)'][i-1]
     
    bt['Cum_return'] = bt['Total_pnl']/500000
    for i in range(1,len(bt['Cum_return'])):
        bt['Cum_return'][i] += bt['Cum_return'][i-1]
    
    bt['Cum_return(no gasfee)'] = (bt['Total_pnl'] + bt['reallowcation fee'])/500000
    for i in range(1,len(bt['Cum_return(no gasfee)'])):
        bt['Cum_return(no gasfee)'][i] += bt['Cum_return(no gasfee)'][i-1]

    bt['Cum_return(no hedge)'] = (bt['Uni_val'] - 500000)/500000
    for i in range(1,len(bt['Cum_return(no hedge)'])):
        bt['Cum_return(no hedge)'][i] += bt['Cum_return(no hedge)'][i-1]


cumret_BH = [bt['Cum_return(B&H)'].loc[bt.index[-1]] for bt in bt_list]
cumret = [bt['Cum_return'].loc[bt.index[-1]] for bt in bt_list]
cumret_NoGas = [bt['Cum_return(no gasfee)'].loc[bt.index[-1]] for bt in bt_list]
cumret_NoHedge = [bt['Cum_return(no hedge)'].loc[bt.index[-1]] for bt in bt_list]

md_BH = [(min(bt['Cum_return(B&H)']) - max(bt['Cum_return(B&H)']))/(max(bt['Cum_return(B&H)'])+1) for bt in bt_list]
md = [(min(bt['Cum_return']) - max(bt['Cum_return']))/(max(bt['Cum_return'])+1) for bt in bt_list]
md_NoGas = [(min(bt['Cum_return(no gasfee)']) - max(bt['Cum_return(no gasfee)']))/(max(bt['Cum_return(no gasfee)'])+1) for bt in bt_list]
md_NoHedge = [(min(bt['Cum_return(no hedge)']) - max(bt['Cum_return(no hedge)']))/(max(bt['Cum_return(no hedge)'])+1) for bt in bt_list]

cum_staking_reward = [sum(bt['Staking_reward']) for bt in bt_list]
cum_reallocation_fee = [sum(bt['reallowcation fee']) for bt in bt_list]
cum_pnl = [sum(bt['Total_pnl']) for bt in bt_list]

dic1 = {'CumRet(B&H)':cumret_BH, 'CumRet':cumret,'CumRet(NoGas)':cumret_NoGas, 'CumRet(NoHedge)':cumret_NoHedge, 'CumPnl':cum_pnl, 'CumEarnFee':cum_staking_reward,'CumReallocationFee':cum_reallocation_fee, 'MDD':md, 'MDD(B&H)':md_BH, 'MDD(NoGas)':md_NoGas, 'MDD(NoHedge)':md_NoHedge}
bt_table = pd.DataFrame(dic1)
bt_table.index = ['high_wide', 'high_narrow', 'low_wide', 'low_narrow']

dfi.export(bt_table, 'BacktestTable.png',dpi=500)


# # Plots

data = pd.read_csv('tx_usdc_eth_3000.csv')
swap = data[data.type=='Swap']
swap['eth_price'] = 1/((1.0001**swap['tick'])/10**12)
swap = swap.reset_index(drop = True)

plt.figure(figsize=(12,6))
plt.plot(pd.to_datetime(swap.Date),swap.eth_price,label='ETH-USDC Price')
plt.xlabel('Date')
plt.ylabel('Price')
plt.title('ETH-USDC Price')
plt.grid()
plt.savefig('./eth_price.jpg',dpi=500)


# ewma price
plt.figure(figsize=(12,6))
plt.plot(pd.to_datetime(swap.Date),swap.eth_price.ewm(span=30).mean(),label='ETH-USDC EWMA Price')
plt.xlabel('Date')
plt.ylabel('Price')
plt.title('ETH-USDC EWMA Price')
plt.grid()
plt.savefig('./eth_price_ewma.jpg',dpi=500)


plt.figure(figsize=(12,6))
plt.plot(pd.to_datetime(bt1.Out_time),bt1['Cum_return(B&H)'],label='Cum_return(B&H)(wide)')
plt.plot(pd.to_datetime(bt1.Out_time),bt2['Cum_return(B&H)'],label='Cum_return(B&H)(narrow)')
plt.plot(pd.to_datetime(bt1.Out_time),bt1['Cum_return'],label='Cum_return(wide)')
plt.plot(pd.to_datetime(bt1.Out_time),bt2['Cum_return'],label='Cum_return(narrow)')
plt.plot(pd.to_datetime(bt1.Out_time),bt1['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(wide)')
plt.plot(pd.to_datetime(bt1.Out_time),bt2['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(narrow)')
plt.xlabel('Date')
plt.ylabel('Return rate')
plt.title('Cumulative Return Rate (HighFreq Split)')
plt.legend()
plt.grid()
plt.savefig('./CumRet_High.jpg',dpi=500)


plt.figure(figsize=(12,6))
plt.plot(pd.to_datetime(bt3.Out_time),bt3['Cum_return(B&H)'],label='Cum_return(B&H)(wide)')
plt.plot(pd.to_datetime(bt3.Out_time),bt4['Cum_return(B&H)'],label='Cum_return(B&H)(narrow)')
plt.plot(pd.to_datetime(bt3.Out_time),bt3['Cum_return'],label='Cum_return(wide)')
plt.plot(pd.to_datetime(bt3.Out_time),bt4['Cum_return'],label='Cum_return(narrow)')
plt.plot(pd.to_datetime(bt3.Out_time),bt3['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(wide)')
plt.plot(pd.to_datetime(bt3.Out_time),bt4['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(narrow)')
plt.xlabel('Date')
plt.ylabel('Return rate')
plt.title('Cumulative Return Rate (LowFreq Split)')
plt.legend()
plt.grid()
plt.savefig('./CumRet_Low.jpg',dpi=500)


# Merge the plots

fig = plt.figure(figsize=(12,6))
ax1 = fig.add_subplot(111)
ax1.plot(pd.to_datetime(bt1.Out_time),bt1['Cum_return(B&H)'],label='Cum_return(B&H)(wide)')
ax1.plot(pd.to_datetime(bt1.Out_time),bt2['Cum_return(B&H)'],label='Cum_return(B&H)(narrow)')
ax1.plot(pd.to_datetime(bt1.Out_time),bt1['Cum_return'],label='Cum_return(wide)')
ax1.plot(pd.to_datetime(bt1.Out_time),bt2['Cum_return'],label='Cum_return(narrow)')
ax1.plot(pd.to_datetime(bt1.Out_time),bt1['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(wide)')
ax1.plot(pd.to_datetime(bt1.Out_time),bt2['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(narrow)')
ax2 = ax1.twinx()
ax2.plot(pd.to_datetime(swap.Date),swap.eth_price,label='ETH-USDC Price')
ax1.legend(loc=0)
ax2.legend(loc=0)
ax1.grid()
ax1.set_xlabel('Date')
ax1.set_ylabel('Return rate')
ax1.set_title('Cumulative Return Rate (HighFreq Split)')
ax2.set_ylabel('Price')
plt.savefig('./CumRetHigh_Price.jpg',dpi=500)


fig = plt.figure(figsize=(12,6))
ax1 = fig.add_subplot(111)
ax1.plot(pd.to_datetime(bt3.Out_time),bt3['Cum_return(B&H)'],label='Cum_return(B&H)(wide)')
ax1.plot(pd.to_datetime(bt3.Out_time),bt4['Cum_return(B&H)'],label='Cum_return(B&H)(narrow)')
ax1.plot(pd.to_datetime(bt3.Out_time),bt3['Cum_return'],label='Cum_return(wide)')
ax1.plot(pd.to_datetime(bt3.Out_time),bt4['Cum_return'],label='Cum_return(narrow)')
ax1.plot(pd.to_datetime(bt3.Out_time),bt3['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(wide)')
ax1.plot(pd.to_datetime(bt3.Out_time),bt4['Cum_return(no gasfee)'],label='Cum_return(no gasfee)(narrow)')
ax2 = ax1.twinx()
ax2.plot(pd.to_datetime(swap.Date),swap.eth_price,label='ETH-USDC Price')
ax1.legend(loc=0)
ax2.legend(loc=0)
ax1.grid()
ax1.set_xlabel('Date')
ax1.set_ylabel('Return rate')
ax1.set_title('Cumulative Return Rate (LowFreq Split)')
ax2.set_ylabel('Price')
plt.savefig('./CumRetLow_Price.jpg',dpi=500)