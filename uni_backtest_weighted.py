import pandas as pd
import numpy as np
import math
import os



def find_tick_for_pool_2(price, decimal0, decimal1):
    tick = int((1 / (-math.log(1.0001, (price * 10 ** decimal0 / 10 ** decimal1))) // 60) * 60)
    return tick



def backtest(swap, alpha, beta):
    # Initialize variables
    cost = 0.0384*2
    idx = 0
    net_val = 500000
    price =  1/1.0001**int(swap.loc[idx].tick)*10**12
    tick_upper = find_tick_for_pool_2(price*np.exp(alpha),6,18)
    tick_lower = find_tick_for_pool_2(price*np.exp(-alpha),6,18)
    price_upper = 1/(1.0001**tick_upper)*10**12
    price_lower = 1/(1.0001**tick_lower)*10**12

    tick_upper_liq = find_tick_for_pool_2(price*np.exp(beta),6,18)
    tick_lower_liq = find_tick_for_pool_2(price*np.exp(-beta),6,18)
    price_upper_liq = 1/(1.0001**tick_upper_liq)*10**12
    price_lower_liq = 1/(1.0001**tick_lower_liq)*10**12
    last_idx = swap.iloc[-1].name
    Eth_amount_init = net_val/(price**0.5 * (price_upper_liq)**0.5 / ((price_upper_liq)**0.5-price**0.5) *(price**0.5-(price_lower_liq)**0.5)+price)
    liquidity = Eth_amount_init* price**0.5 * (price_upper_liq)**0.5 / ((price_upper_liq)**0.5-price**0.5)
    USDC_amount_init = liquidity *(price**0.5-(price_lower_liq)**0.5)
    # Start backtesting
    info_columns = ['Tick', 'Side', 'Out_time', 'Staking_reward', 'Price', 'ETH_amount', 'Uni_val','B&H','reallowcation fee']
    info_df = pd.DataFrame(columns=info_columns)
    info_df.loc[0] = [swap.tick[0],0,swap.Date[idx],0,price,Eth_amount_init,500000,500000,0]
    iter = 0
    reallowcation_fee = 0
    Net_val_arr = []
    while (idx < last_idx):
        #update variables according to idx
        iter += 1
        print('Enter position', iter)
        info_in_loop = [] #每次breakout再投入都重置
        tick = swap.loc[idx].tick
        info_in_loop.append(tick)
        price = 1 / 1.0001 ** int(tick) * 10 ** 12
        tick_upper = find_tick_for_pool_2(price*(1+alpha),6,18)
        tick_lower = find_tick_for_pool_2(price*(1-alpha),6,18)
        price_upper = 1/(1.0001**tick_upper)*10**12
        price_lower = 1/(1.0001**tick_lower)*10**12
        
        tick_upper_liq = find_tick_for_pool_2(price*(1+beta),6,18)
        tick_lower_liq = find_tick_for_pool_2(price*(1-beta),6,18)
        price_upper_liq = 1/(1.0001**tick_upper_liq)*10**12
        price_lower_liq = 1/(1.0001**tick_lower_liq)*10**12
        #initialize the position
        Eth_amount = net_val/(price**0.5 * (price_upper_liq)**0.5 / ((price_upper_liq)**0.5-price**0.5) *(price**0.5-(price_lower_liq)**0.5)+price)
        liquidity = Eth_amount * price**0.5 * (price_upper_liq)**0.5 / ((price_upper_liq)**0.5-price**0.5)
        USDC_amount = liquidity *(price**0.5-(price_lower_liq)**0.5)
        lx = Eth_amount*price**0.5*price_upper_liq**0.5/(price_upper_liq**0.5-price**0.5)
        ly = USDC_amount/(price**0.5-price_lower_liq**0.5)
        liquidity = min(lx,ly)
        swap_proxy = swap[idx:]
        prev_idx = idx
        idx_1 = swap_proxy[swap_proxy.tick <= tick_upper].first_valid_index() if (swap_proxy[swap_proxy.tick <= tick_upper].first_valid_index()) else last_idx
        idx_2 = swap_proxy[swap_proxy.tick >= tick_lower].first_valid_index() if (swap_proxy[swap_proxy.tick >= tick_lower].first_valid_index()) else last_idx
        idx = min(idx_1,idx_2) #update idx of break out
        if idx_1 == idx_2: # ==last_idx
            info_in_loop.append(0.5) #按columns顺序append
            price = 1 / 1.0001 ** int(swap_proxy.loc[idx].tick) * 10 ** 12
            if(price>=price_upper_liq):
                net_val = liquidity * (price_upper_liq ** 0.5 - price_lower_liq ** 0.5)
            elif(price<=price_lower_liq):
                net_val = (price_upper_liq ** 0.5 - price_lower_liq ** 0.5) / (price_upper_liq ** 0.5 * price_lower_liq ** 0.5) * liquidity * price
            else:
                x_amount = (price_upper_liq ** 0.5 - price ** 0.5) / (price_upper_liq ** 0.5 * price ** 0.5) * liquidity
                y_amount = liquidity * (price ** 0.5 - price_lower_liq ** 0.5)
                net_val = y_amount+ x_amount*price
        elif idx_2 == idx:
            info_in_loop.append(0)
            price = 1 / 1.0001 ** int(swap_proxy.loc[idx].tick) * 10 ** 12
            net_val = (price_upper_liq ** 0.5 - price_lower_liq ** 0.5) / (price_upper_liq ** 0.5 * price_lower_liq ** 0.5) * liquidity * price
        elif idx_1 == idx:
            info_in_loop.append(1)
            net_val = liquidity * (price_upper_liq ** 0.5 - price_lower_liq ** 0.5)
            
        time_out = int(pd.Timestamp(swap_proxy.Date[idx]).timestamp())
        info_in_loop.append(pd.to_datetime(time_out, unit='s')) #按info的columns的顺序，这里记录time_out时间
        
        #计算fee earned
        x_amount_in = Eth_amount
        x_amount_out = 0
        y_amount_in = USDC_amount
        y_amount_out = 0
        staking_reward_0 = 0
        staking_reward_1 = 0
        tick_prev = tick
        price =  1/1.0001**int(tick)*10**12
        for i in swap[prev_idx:idx].tick: # 从intialize到下一个go across的time interval #i遍历了一组tick_per_idx为元素的list #计算每个idx累积了多少fee
            if(i<=tick_upper_liq): #outside upper liquidity bound
                y_amount_out = liquidity * (price_upper_liq ** 0.5 - price_lower_liq ** 0.5)
                x_amount_out = 0
                Net_val_arr.append(y_amount_out)
            elif(i>=tick_lower_liq): #outside lower liquidity bound
                y_amount_out = 0
                x_amount_out = liquidity*(price_upper_liq ** 0.5 - price_lower_liq ** 0.5) / (price_upper_liq ** 0.5 * price_lower_liq ** 0.5)
                Net_val_arr.append(x_amount_out * (1/1.0001**int(i)*10**12)) 
            else: #tick还在或回到了liq interval中
                lx = x_amount_in*price**0.5*price_upper_liq**0.5/(price_upper_liq**0.5-price**0.5)
                ly = y_amount_in/(price**0.5-price_lower_liq**0.5)
                price =  1/1.0001**int(i)*10**12
                liquidity = min(lx,ly)
                x_amount_out =  (price_upper_liq ** 0.5 - price ** 0.5) / (price_upper_liq ** 0.5 * price ** 0.5) * liquidity
                y_amount_out = liquidity * (price ** 0.5 - price_lower_liq ** 0.5)
                if(i>= tick_prev): #tick上涨时在x token上累积的fee
                    staking_reward_1 += abs((x_amount_out-x_amount_in))*0.003
                else: #tick下跌时在y token上累积的fee
                    staking_reward_0 += abs((y_amount_out-y_amount_in))*0.003
                tick_prev = i #update tick_prev
                Net_val_arr.append(x_amount_out*price + y_amount_out+staking_reward_1*price+staking_reward_0) #记录不跳出break interval前的net_val随swap的变化
                x_amount_in = x_amount_out
                y_amount_in = y_amount_out
        
        price = 1/1.0001**int(swap.loc[idx].tick)*10**(12)
        net_val = net_val+staking_reward_0+staking_reward_1*price- cost*price #the real net value when subperiod ends
        reallowcation_fee += cost*price
        info_in_loop.append(staking_reward_0 + staking_reward_1 * price)
        info_in_loop.append(price)
        info_in_loop.append(Eth_amount) #每次break out后投入时at initial的eth amount
        info_in_loop.append(net_val)
        info_in_loop.append(Eth_amount*price+USDC_amount-cost*price) #buy and hold的pnl
        info_in_loop.append(reallowcation_fee)
        info_df.loc[len(info_df)] = info_in_loop #dataframe一行一行的填入info_in_loop每次循环的一组元素
    #单个subperiod里有很多次break out，但只有最后结束才整理计算总的指标，中间break out再投入都保持记录
    #subperiod的bt结束，计算指标
    info_df['Hedge_pnl'] = -(info_df['Price'] - info_df['Price'].shift(1)) * info_df['ETH_amount'] #用diff也行
    info_df['Total_val'] = info_df['Uni_val']
    for i in range(len(info_df)):
        info_df['Total_val'].iloc[i] += (info_df['Hedge_pnl'].iloc[:i].sum() + info_df['Hedge_pnl'].iloc[i]) # 
    info_df['Total_pnl'] = info_df['Total_val'] - 500000
    info_df['alpha'] = alpha
    info_df['beta'] = beta
    s = pd.Series(Net_val_arr)
    p = s.diff() / s.shift(1) # net_val转为return_rate
    info_df['sharp ratio'] = np.mean(p)/np.std(p)
    info_df['B&H'] = info_df['Price']*Eth_amount_init + USDC_amount_init #全是init，中间BH不调仓的，每个subperiod（指的是split）里BH保持仓位不变
    # LP策略里 每次breakout后 依旧用alpha和beta以最新tick和最新net_val为资金投入池子
    return info_df


def find_optimal_width(swap, width_list,split_num,window):
    df = swap.copy()
    df = df.reset_index(drop=True)
    backtest_dict = {}
    for i in width_list:
        alpha = i
        for j in width_list:
            if(j<=i):
                print('------------------------')
                print('Optimaling:[',i,',',j,']')
                print('------------------------')
                beta = j
                sharp = 0
                for k in range(split_num): #object function
                    sharp = backtest(df[k*window:(k+1)*window].reset_index(drop=True), alpha, beta)['sharp ratio'].iloc[-1] * 0.96+0.04*sharp #只用前一个窗口的信息最优化，而不是用前面所有时间所有窗口所有信息
                backtest_dict[sharp] = [[i,j]]   
    backtest_dict = {k: v for k, v in backtest_dict.items() if k != 0} #筛除k=0的键值对
    optimal_width = backtest_dict[max(backtest_dict)][0] #find最大key（最大sharp ratio），取value这个list的0号index，也就是[i,j]
    print('~~~~~~~~~~~~~~~~~~~~~~~')
    print('Optimal Width:', optimal_width)
    print('~~~~~~~~~~~~~~~~~~~~~~~')
    return optimal_width


def rolling_backtest(swap, split, width_list):
    swap = swap.reset_index(drop=True)
    window = len(swap) // split
    final_df = pd.DataFrame()
    split_num = 0
    for index in list(range(window, len(swap), window)): #rolling的，不是full info
        split_num += 1
        print('########################################################')
        print('Enter split:', split_num)
        print('########################################################')
        optimized_width = find_optimal_width(swap.iloc[0:index].reset_index(drop=True),width_list,split_num,window)
        split_df = backtest(swap.iloc[index:index+window].reset_index(drop=True), optimized_width[0], optimized_width[1])
        split_df.to_csv('Split_' + str(split_num) + '_Result.csv')
        # if final_df.empty:
        #     final_df = split_df.iloc[-1]
        # else:
        #     final_df = final_df.append(split_df.iloc[-1])
        final_df = final_df.append(split_df.iloc[-1])
    return final_df


def generate_dir(name):
    if not os.path.isdir(name):
        os.mkdir(name)
    os.chdir(name)


if __name__ == "__main__":
    #### Initial path (need to change)
    initial_path = '/Users/emersonlee/Desktop/Python_File/BT1028/'
    # Parameters
    split_short = 12
    split_long = 24
    width_list_short = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    width_list_long = [0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15]
    # Transport

    # Pool - 0.3%
    # 创建分类的文件夹
    os.chdir(initial_path)
    data = pd.read_csv('tx_usdc_eth_3000.csv')
    swap = data[data.type == 'Swap']
    generate_dir('Pool_0.3% EWMA')
    generate_dir('split_short')
    generate_dir('width_list_short')
    result = rolling_backtest(swap, split_short, width_list_short)
    result.to_csv('Backtest_result.csv')
    os.chdir(initial_path + 'Pool_0.3% EWMA')
    generate_dir('split_short')
    generate_dir('width_list_long')
    result = rolling_backtest(swap, split_short, width_list_long)
    result.to_csv('Backtest_result.csv')
    os.chdir(initial_path + 'Pool_0.3% EWMA')
    generate_dir('split_long')
    generate_dir('width_list_short')
    result = rolling_backtest(swap, split_long, width_list_short)
    result.to_csv('Backtest_result.csv')
    os.chdir(initial_path + 'Pool_0.3% EWMA')
    generate_dir('split_long')
    generate_dir('width_list_long')
    result = rolling_backtest(swap, split_long, width_list_long)
    result.to_csv('Backtest_result.csv')



