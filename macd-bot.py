import time

import pandas as pd

from binance.client import Client
from time import sleep
from binance import ThreadedWebsocketManager

import os
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

client = Client() ### KEY DELETED for privacy
client.API_URL = 'https://testnet.binance.vision/api'

### returns MACD - signal line  OR  False if bad input
def getMACDDiff():
    ema12_data = client.get_historical_klines("ETHUSDT", "1m", "30 min ago UTC") #get 18 extra points for sma, ema, and macd calculations
    ema26_data = client.get_historical_klines("ETHUSDT", "1m", "44 min ago UTC")

    if len(ema12_data) != 30:
        return False
    if len(ema26_data) != 44:
        return False
    ### INITIAL SMA FOR EMA
    sum_12 = 0.0
    i = 0
    while i < 12:
        sum_12 += float(ema12_data[i][4])
        i += 1

    init_sma12 = sum_12 / 12.0

    ### CALCULATE EMA ###
    ema12_points = []
    ema12 = init_sma12
    k = 2/13 #constant for ema

    while i<30: #i from 12 to 25
        ema12 = (float(ema12_data[i][4])*k) + (ema12*(1-k))
        ema12_points.append(ema12)
        i += 1

    ### INITIAL SMA FOR EMA
    sum_26 = 0.0
    i = 0
    while i < 26:
        sum_26 += float(ema26_data[i][4])
        i += 1

    init_sma26 = sum_26 / 26.0

    ### CALCULATE EMA
    ema26 = init_sma26
    k = 2 / 27  # constant for ema
    ema26_points = []

    while i < 44:  # i from 26 to 52
        ema26 = (float(ema26_data[i][4]) * k) + (ema26 * (1 - k))
        ema26_points.append(ema26)
        i += 1

    ### Create MACD list
    macd_points = []
    i = 0
    while i < 18:
        macd = ema12_points[i] - ema26_points[i]
        macd_points.append(macd)
        i += 1

    ## Get Signal Line SMA
    signal_sum = 0.0
    i = 0
    while i < 9:
        signal_sum += float(macd_points[i])
        i += 1

    signal_sma = signal_sum / 9.0

    ## Calculate signal line
    signal_point = signal_sma
    k = 2 / 10  # constant for ema calculation

    while i < 18:  # i from 9 to 18
        signal_point = (macd_points[i] * k) + (signal_point * (1 - k))
        i += 1

    ##print signal and macd
    # print("MACD:", macd_points[len(macd_points) - 1])
    # print("Signal:", signal_point)
    return macd_points[len(macd_points) - 1] - signal_point

def testTrade():
    if not getMACDDiff():
        print("Unexpected API data")
        return False
    if getMACDDiff() < 0:
        print("Waiting for buy signal...")
        while True:
            time.sleep(0.5)
            if not getMACDDiff():
                print("Unexpected API data")
                continue
            if getMACDDiff() > 0: #waits for a cross
                buy_price = client.get_symbol_ticker(symbol="ETHUSDT")['price']
                buy_price = float(buy_price)
                print("BUYING ETH at:", buy_price)
                buyOrder = test_buy(buy_price)
                buyOrderId = buyOrder['orderId']
                print(buyOrder)
                break
        orderStatus = client.get_order(symbol="ETHUSDT",orderId=buyOrderId)


        target_price = buy_price * 1.0015
        fail_price = buy_price * 0.9985
        print("Selling at", target_price, "or", fail_price)
        while True:
            time.sleep(0.1)
            curr_price = client.get_symbol_ticker(symbol="ETHUSDT")['price']
            curr_price = float(curr_price)

            if curr_price >= target_price or curr_price <= fail_price:
                sell_order = test_sell(curr_price)
                print("Sell Order:")
                print(sell_order)
                return sell_order

    else:
        print("MACD above signal...")
        return False




def test_buy(limit):
    try:
        qty = (20.0 / limit).__round__(7)
        qty = float(qty)
        qty = 0.05
        buy_limit = client.create_order(
            symbol='ETHUSDT',
            side='BUY',
            type='LIMIT',
            timeInForce='GTC',
            quantity=qty,  # 20 USD worth of ETH
            price=limit)
        return buy_limit
        # buy_market = client.create_test_order(symbol='ETHUSDT', side='BUY', type='MARKET', quantity=0.05)
        # print(buy_market)
        # return buy_market

    except BinanceAPIException as e:
        # error handling goes here
        print(e)
        return False
    except BinanceOrderException as e:
        # error handling goes here
        print(e)
        return False


def test_sell(limit):
    try:
        qty = (20.0 / limit).__round__(7)
        qty = float(qty)
        qty = 0.05
        sell_limit = client.create_order(
            symbol='ETHUSDT',
            side='SELL',
            type='LIMIT',
            timeInForce='GTC',
            quantity=qty,  # 20 USD worth of ETH -- confused on how to do this
            price=limit)
        return sell_limit

    except BinanceAPIException as e:
        # error handling goes here
        print(e)
        return False
    except BinanceOrderException as e:
        # error handling goes here
        print(e)
        return False

initial = client.get_account()
print(initial)

print(client.get_open_orders(symbol="ETHUSDT"))

while True:
    trade = testTrade()
    if trade != False:
        break
    time.sleep(10)

time.sleep(3)
orderID = trade['orderId']

while True:
    testOrder = client.get_order(symbol="ETHUSDT", orderId=orderID)
    if testOrder["status"] == "FILLED":
        break
    time.sleep(3)
    print("Order not filled")
    # print("Cancelling")
    # client.cancel_order(symbol="ETHUSDT", orderId=orderID)



time.sleep(5) #if order fills
print("Initial account data:")
print(initial)
print("Current account data:")
print(client.get_account()) #results
