import ccxt
from binance.client import Client
import config
import csv
import schedule
from openpyxl import Workbook
import pandas as pd
pd.set_option('display.max_rows', None)
import warnings
warnings.filterwarnings('ignore')
import numpy as np
from datetime import datetime
import time
global leverage
market=input ( "Enter the desired market:" )
amt=float(input("Enter the desired quantity of tokens you want to buy/sell in each position:"))
leverage=int(input("Enter leverage: "))
long_tp=int(input("Enter Long Take Profit(x/10000): = "))
short_tp=int(input("Enter Short Take Profit(x/10000): = "))
precision=int(input("Enter Precision:"))
long_tp=long_tp/1000+1
short_tp=abs(short_tp/1000-1)

    #KALDIRAÇI AŞAĞIDAN BİR DAHA AYARLAMAN GEREK
in_position = False
short_position= False
long_position=False

def tr(data):
    data['previous_close'] = data['close'].shift(1)
    data['high-low'] = abs(data['high'] - data['low'])
    data['high-pc'] = abs(data['high'] - data['previous_close'])
    data['low-pc'] = abs(data['low'] - data['previous_close'])

    tr = data[['high-low', 'high-pc', 'low-pc']].max(axis=1)

    return tr

def atr(data, period):
    data['tr'] = tr(data)
    atr = data['tr'].rolling(period).mean()

    return atr

def supertrend(df, period=7, atr_multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    df['atr'] = atr(df, period)
    df['upperband'] = hl2 + (atr_multiplier * df['atr'])
    df['lowerband'] = hl2 - (atr_multiplier * df['atr'])
    df['in_uptrend'] = True

    for current in range(1, len(df.index)-1):
        previous = current - 1
        if df['close'][current] > df['upperband'][previous]:
            df['in_uptrend'][current] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df['in_uptrend'][current] = False
        else:
            df['in_uptrend'][current] = df['in_uptrend'][previous]

            if df['in_uptrend'][current] and df['lowerband'][current] < df['lowerband'][previous]:
                df['lowerband'][current] = df['lowerband'][previous]

            if not df['in_uptrend'][current] and df['upperband'][current] > df['upperband'][previous]:
                df['upperband'][current] = df['upperband'][previous]
    return df

def check_if_enough_margin(last_close,amt):
    client=Client(config.public_key,config.secret_key, {"timeout": 40})    
    holder=client.futures_account_balance()
    balance=float(holder[6]["balance"])
    naked_amount=balance/last_close
    maximum=float(naked_amount*leverage)
    if amt>maximum:
        amt=maximum*0.95
        round(amt,4)
        print("Margin changed")
    else:
        print("Margin remain same")
    return amt

def failsafe(upperband,lowerband,markprice,client):
    if in_position:
        if markprice>upperband*1.015 and short_position:
            client.futures_create_order(symbol=market,side="BUY",positionSide = "SHORT",type="MARKET",quantity=1000)
        if markprice<lowerband*0.985 and long_position:
            client.futures_create_order(symbol=market,side="SELL",positionSide = "LONG",type="MARKET",quantity=1000)

def check_for_positions(client):
    global in_position
    global short_position
    global long_position
    in_position = False
    short_position= False
    long_position=False
    info=client.futures_position_information(symbol=market)
    Short=float(info[2]["positionAmt"])
    Long=float(info[1]["positionAmt"])
    if Short<0:
        short_position=True
        in_position=True
        long_position=False
        print(f"Short position of :{Short}")
    if Long>0:
        short_position=False
        in_position=True
        long_position=True
        print(f"Long position of :{Long}")
    if Short==Long==0:
        in_position = False
        short_position= False
        long_position=False
        print(f"Not in position")
            
def check_buy_sell_signals(df,amt,mark_price,long_tp,short_tp):
    client=Client(config.public_key,config.secret_key, {"timeout": 40})
    data=supertrend(df)
    for current in range(1, len(data.index)):
        previous = current - 1
    last_row_index = len(df.index) - 2
    previous_row_index = last_row_index - 1
    failsafe(data["upperband"][last_row_index],data["lowerband"][last_row_index],mark_price,client)    
    print("checking for buy and sell signals")
    print(df.tail(5))
    print(mark_price)
    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("Changed to uptrend")
        amt=check_if_enough_margin(mark_price,amt)
        if not in_position:
            print("Getting into Long position")
            client=Client(config.public_key,config.secret_key, {"timeout": 40})
            client.futures_cancel_all_open_orders(symbol=market)
            order = client.futures_create_order(symbol=market,side="BUY",positionSide = "LONG",type="MARKET",quantity=amt)
            stop_loss = client.futures_create_order(symbol=market,side='SELL',type='STOP_MARKET',quantity = amt,positionSide = "LONG",stopPrice =round(data["lowerband"][current],4) , closePosition = True)
            order_take = client.futures_create_order(symbol=market,side='SELL', type='TAKE_PROFIT_MARKET',quantity = amt,positionSide = "LONG", stopPrice =round(mark_price*long_tp,4) ,closePosition=True)
            loss=stop_loss["orderId"]
            profit=order_take["orderId"]
            print(order)
        if in_position and short_position:
           client=Client(config.public_key,config.secret_key, {"timeout": 40})
           print("Getting out of Short, Entering Long")
           client.futures_cancel_all_open_orders(symbol=market)
           a=client.futures_position_information(symbol=market)
           if float(a[2]["positionAmt"])<0:
               client.futures_create_order(symbol=market,side="BUY",positionSide = "SHORT",type="MARKET",quantity=1000)
           order = client.futures_create_order(symbol=market,side="BUY",positionSide = "LONG",type="MARKET",quantity=amt)
           stop_loss = client.futures_create_order(symbol=market,side='SELL',type='STOP_MARKET',quantity = amt,positionSide = "LONG",stopPrice =round(data["lowerband"][current],4) , closePosition = True)
           order_take = client.futures_create_order(symbol=market,side='SELL', type='TAKE_PROFIT_MARKET',quantity = amt,positionSide = "LONG", stopPrice =round(mark_price*long_tp,4) ,closePosition=True)
           loss=stop_loss["orderId"]
           profit=order_take["orderId"]
        else:
            print("already in position, nothing to do")
    
    if df['in_uptrend'][previous_row_index] and not df['in_uptrend'][last_row_index]:
        amt=check_if_enough_margin(mark_price,amt)
        print("Changed to Downtrend")
        if in_position and long_position:
            client=Client(config.public_key,config.secret_key, {"timeout": 40})  
            print("Getting out of long, Entering Short")
            client.futures_cancel_all_open_orders(symbol=market)
            a=client.futures_position_information(symbol=market)
            if float(a[1]["positionAmt"])>0:
                client.futures_create_order(symbol=market,side="SELL",positionSide = "LONG",type="MARKET",quantity=1000)
            order = client.futures_create_order(symbol=market,side="SELL",positionSide = "SHORT",type="MARKET",quantity=amt)
            order_take=client.futures_create_order(symbol=market,side="BUY",type="TAKE_PROFIT_MARKET",quantity=amt,positionSide="SHORT",stopPrice=round(mark_price*short_tp,4),closePosition=True)
            stop_loss=client.futures_create_order(symbol=market,side="BUY",type="STOP_MARKET",quantity=amt,positionSide="SHORT",stopPrice=round(data["upperband"][current],4),closePosition=True)
        if not in_position and not short_position:
            print("Getting into short position")
            client=Client(config.public_key,config.secret_key, {"timeout": 40})
            client.futures_cancel_all_open_orders(symbol=market)
            order = client.futures_create_order(symbol=market,side="SELL",positionSide = "SHORT",type="MARKET",quantity=amt)
            stop_loss=client.futures_create_order(symbol=market,side="BUY",type="STOP_MARKET",quantity=amt,positionSide="SHORT",stopPrice=round(data["upperband"][current],4),closePosition=True)
            order_take=client.futures_create_order(symbol=market,side="BUY",type="TAKE_PROFIT_MARKET",quantity=amt,positionSide="SHORT",stopPrice=round(mark_price*short_tp,4),closePosition=True)
        if in_position and short_position:
            print("Already in short")
def excel(client):
    wb = load_workbook(filename = 'Bohoyt.xlsx')
    ws=wb.active

    if long_position:
        info=client.futures_position_information(symbol=market)
        orders=client.futures_get_open_orders(symbol=market)
        if orders[1]["type"]=="TAKE_PROFIT_MARKET":
            tp=float(orders[1]["stopPrice"])
        if orders[2]["type"]=="TAKE_PROFIT_MARKET":
            tp=float(orders[2]["stopPrice"])
        entry=float(info[1]["entryPrice"])


def run_bot():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    client=Client(config.public_key,config.secret_key, {"timeout": 40})
    bars = client.futures_klines(symbol=market, interval=Client.KLINE_INTERVAL_3MINUTE)
    for x in bars:
        del x[6:12]
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',], dtype=float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    mark_price=client.futures_mark_price(symbol=market)
    mark_price=float(mark_price["markPrice"])
    qty=amt/mark_price
    qty=round(qty*leverage,1)
    qty=round(qty,precision)
    print(f"Volume of position: {qty}")
   # if in_position:
   # excel(client)
    supertrend_data = supertrend(df)
    check_for_positions(client)
    check_buy_sell_signals(supertrend_data,qty,mark_price,long_tp,short_tp)
schedule.every(2).seconds.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)