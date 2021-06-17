import time
import datetime
import pytz
import pyupbit
import numpy as np
import pandas as pd
import schedule



""" Modify here! """
interval = 30 # Minutes
my_interval = "minute" + str(interval)


access = "gTrRO1Ypp4Vjsgzup1uAxXq97gBCSouvGGushkmB"
secret = "drOzjJbBm4WSRhhZ3JguEfaroiJRgsLLeAxAbSHL"


def get_tickers_global():
    tickers_KRW_global = pyupbit.get_tickers(fiat="KRW")
    exclusions = ['MARO', 'PCI','OBSR','SOLVE','QTCON', 'BTC', 'ETH', 
                  'KMD', 'ADX', 'LBC', 'IGNIS', 'DMT', 'EMC2', 'TSHP', 'LAMB', 'EDR', 'PXL']

    for exclusion in exclusions:
        exclusion_KRW = 'KRW-' + exclusion

        tickers_KRW_global.remove(exclusion_KRW)
        
    return tickers_KRW_global


def get_df_dictionary():
    
    tickers_KRW_global = get_tickers_global()
    df_dictionary = {}
    for ticker_KRW in tickers_KRW_global:
        ticker = ticker_KRW[4:]
        df = pyupbit.get_ohlcv(ticker_KRW, interval=my_interval, count = 60, period=0.1)
        time.sleep(0.1)
        df_dictionary[ticker] = df[:-1]
    return df_dictionary


def get_ma_prev(df, ma, prev):
    if prev == 0:
        df_ma = df[-ma-prev:]
    else:
        df_ma = df[-ma-prev:-prev]

    return round( df_ma['close'].rolling(ma).mean().iloc[-1], 2)


def get_dictionary_bool_list(df, bool_list_num):
    dictionary_bool_list = []
    for idx in range(bool_list_num+1):
        # print(df.iloc[-1-idx]['close'])
        # print(get_ma_prev(df, 20, idx))
        # print(idx)
        # print(df.iloc[-1-idx]['close'] > get_ma_prev(df, 20, idx))
        dictionary_bool_list.append( df.iloc[-1-idx]['close'] > get_ma_prev(df, 20, idx) )
        # print(idx)
        # dictionary_bool_list.append( get_ma_prev(df, 20, idx) )
        # print(dictionary_bool_list)
    dictionary_bool_list.reverse()
        
    return dictionary_bool_list


def get_balance(ticker):
    balances = upbit.get_balances()
    time.sleep(0.1)
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
            
def get_start_time(my_interval):
    df = pyupbit.get_ohlcv("KRW-ETH", interval=my_interval, count=1)
    start_time = df.index[0]
    return start_time

def get_price(raw):
    if raw < 10:
        target_price = round(raw, 2)
    elif raw < 100:
        target_price = round(raw, 1)
    elif raw < 1000:
        target_price = round(raw, 0)
    elif raw < 100000:
        target_price = round(raw, -1)
    elif raw < 10000000:
        target_price = round(raw, -2)
    elif raw < 1000000000:
        target_price = round(raw, -3)
        
    return target_price

#%%

bool_list_num = 30
selling_point = 8 # %
duration = 24
buy_KRW = 10000

upbit = pyupbit.Upbit(access, secret)

# bool_list = [0,0,0,0,0,1]
bool_list = [0]*bool_list_num
bool_list.append(1)
# bool_list_array = np.asarray(bool_list).reshape((bool_list_num+1, 1))

# Initialize dictionary
dictionary = {}
tickers_KRW_global = get_tickers_global()
for ticker_KRW in tickers_KRW_global:
    ticker = ticker_KRW[4:]
    dictionary[ticker] = [0]*(5+bool_list_num+1)


print("autotrade start")
while True:
    
    # Update dictionary
    df_dictionary1 = get_df_dictionary()
    print('dictionary1')
    df_dictionary2 = get_df_dictionary()
    print('dictionary2')
    if df_dictionary1['ADA'].iloc[0, [5]].item() == df_dictionary2['ADA'].iloc[0, [5]].item():
        df_dictionary = df_dictionary2
    else:
        print(f'Next time step at {datetime.datetime.now()}') 
        time.sleep(60)
        df_dictionary = get_df_dictionary()
        # print(dictionary)

    for ticker_KRW in tickers_KRW_global:
        ticker = ticker_KRW[4:]
        df = df_dictionary[ticker]
        # close = df.iloc[-1]['close']
 
        dictionary[ticker][5:] = get_dictionary_bool_list(df, bool_list_num)
    
    print('buy')
    # BUY
    for ticker_KRW in tickers_KRW_global:
        ticker = ticker_KRW[4:]
        # print(dictionary[ticker][1:7])
        if dictionary[ticker][5:] == bool_list and dictionary[ticker][0] == 0:
            
            # df = df_dictionary[ticker]
            # close = df.iloc[-1]['close']
            # if close > get_ma_prev(df, 20, 0): # Buy market order
                
            krw = get_balance("KRW")
            crypto = get_balance(ticker)
            if krw > 1000000: 

                order = upbit.get_order(ticker_KRW)
                if len(order) == 0:
                    upbit.buy_market_order(ticker_KRW, buy_KRW)
                    
                    # update dictionary
                    buy_price = pyupbit.get_current_price(ticker_KRW)
                    start_time = get_start_time(my_interval)
                    end_time = start_time + datetime.timedelta(hours=24)
                    dictionary[ticker][0:4] = [1, buy_price, start_time, end_time]
                    print(f"Buy order placed for {ticker} at price: {buy_price}")
                        

    print('sell')
    # SELL order place
    for ticker_KRW in tickers_KRW_global:
        ticker = ticker_KRW[4:]
        
        if dictionary[ticker][0] == 1:
            order = upbit.get_order(ticker_KRW)
            if len(order) == 0:
                buy_price = dictionary[ticker][1]
                sell_price = get_price( buy_price*(1+selling_point*0.01) )
                crypto = get_balance(ticker)
                upbit.sell_limit_order(ticker_KRW, sell_price, crypto)
                print(f"Sell order placed for {ticker} at price: {sell_price}")
                
                # Update dictionary
                dictionary[ticker][4] = 1
    
    print('sell check')
    # Sell check
    for ticker_KRW in tickers_KRW_global:
        ticker = ticker_KRW[4:]
    
        order = upbit.get_order(ticker_KRW)
        if len(order) == 0: # Sold out
            dictionary[ticker][:5] = [0,0,0,0,0]
    
        else:
            now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul'))

            start_str = order[0]['created_at'][2:-6]
            start_time = datetime.datetime.strptime(start_str, '%y-%m-%dT%H:%M:%S').astimezone(pytz.timezone('Asia/Seoul'))
            # start_time = start_time - datetime.timedelta(hours=9) # Activate if it runs at cloud
            end_time = start_time + datetime.timedelta(hours=duration*0.5)
            
            if now > end_time: # Fail to sell during the duration
                upbit.cancel_order(order[0]['uuid'])
                print(f"Order for {ticker} deleted and sold")
                time.sleep(2)
                crypto = get_balance(ticker)
                upbit.sell_market_order(ticker_KRW, crypto)
                dictionary[ticker][:5] = [0,0,0,0,0]






