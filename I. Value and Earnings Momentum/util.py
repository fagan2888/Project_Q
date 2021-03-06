# -*- coding: utf-8 -*-
"""
Created on Fri May 24 08:20:52 2019

@author: woojin
"""

import os
import pandas as pd
import numpy as np
import datetime
import pymysql
import xlrd
import time
import sys
from tqdm import tqdm
import calendar

def data_cleansing(rawData):
    '''Quantiwise 제공 재무데이터 클렌징 용도
    YYYYMM 형태로 데이터가 나오기 때문에 yyyy-mm-dd 로 변경 (dd는 말일 날짜)
    '''
    firmCode = rawData.iloc[7,5:].values
    yearIndex = [int(str(x)[:4]) for x in rawData.iloc[10:,1].values]
    monthIndex = [int(str(x)[4:]) for x in rawData.iloc[10:,1].values]
    newDateIndex = []
    for i in range(len(yearIndex)):
        days = calendar.monthrange(yearIndex[i], monthIndex[i])[1]
        newDateIndex.append(datetime.datetime(yearIndex[i], monthIndex[i], days))
    
    newData = rawData.iloc[10:,5:]
    newData.columns = firmCode
    newData.index = newDateIndex
    
    return newData

def data_cleansing_ts(rawData):
    '''Quantiwise 제공 시계열데이터 클렌징 용도
    - 열 : 종목명
    - 행 : 시계열
    '''    
    firmCode = rawData.iloc[6, 1:].values
    dateIndex = rawData.iloc[13:, 0].values
    newData = rawData.iloc[13:,1:]
    newData.columns = firmCode
    newData.index = dateIndex
    return newData

def get_stock_price(stockCodes, date_start, date_end):
    '''
    input: 
    - stockcodes : list
    - date_start : datetime
    - date_end : datetiem
    
    output : DataFrame
    - Index : Stock code
    - value : Stock Price
    '''
    date_start = ''.join([x for x in str(date_start)[:10] if x != '-'])
    date_end = ''.join([x for x in str(date_end)[:10] if x != '-'])
    db = pymysql.connect(host='192.168.1.190', port=3306, user='root', passwd='gudwls2@', db='quant_db',charset='utf8',autocommit=True)
    cursor = db.cursor()
    joined = "\',\'".join(stockCodes)
    sql = "SELECT GICODE, TRD_DT, ADJ_PRC FROM dg_fns_jd WHERE TRD_DT BETWEEN " + date_start
    sql += ' AND ' + date_end
    sql += (" AND GICODE IN (\'" + joined + "\')")
    cursor.execute(sql)
    data = cursor.fetchall()
    data = pd.DataFrame(list(data))
    data = data.pivot(index = 1, columns = 0, values = 2)
    data.index = pd.to_datetime(data.index.values)
    db.close()   
    return data


def get_index_price(stockCodes, date_start, date_end):
    '''
    input: 
    - stockcodes : list
    - date_start : datetime
    - date_end : datetiem
    
    output : DataFrame
    - Index : Stock code
    - value : Stock Price
    '''
    date_start = ''.join([x for x in str(date_start)[:10] if x != '-'])
    date_end = ''.join([x for x in str(date_end)[:10] if x != '-'])
    db = pymysql.connect(host='192.168.1.190', port=3306, user='root', passwd='gudwls2@', db='quant_db',charset='utf8',autocommit=True)
    cursor = db.cursor()
    joined = "\',\'".join(stockCodes)
    sql = "SELECT U_CD, TRD_DT, CLS_PRC FROM dg_udsise WHERE TRD_DT BETWEEN " + date_start
    sql += ' AND ' + date_end
    sql += (" AND U_CD IN (\'" + joined + "\')")
    cursor.execute(sql)
    data = cursor.fetchall()
    data = pd.DataFrame(list(data))
    data = data.pivot(index = 1, columns = 0, values = 2)
    data.index = pd.to_datetime(data.index.values)
    db.close()   
    return data

def get_amt_money(weightList, totalMoney):
    '''
    weightList : array
    totalMoney : scalar
    '''    
    return weightList * totalMoney

def get_recentBday(date):
    
    date = ''.join([x for x in str(date)[:10] if x != '-'])
    db = pymysql.connect(host='192.168.1.190', port=3306, user='root', passwd='gudwls2@', db='quant_db',charset='utf8',autocommit=True)
    cursor = db.cursor()    
    sql = "SELECT DISTINCT TRD_DT FROM dg_fns_jd WHERE TRD_DT <=" + date 
    sql += " ORDER BY TRD_DT"
    cursor.execute(sql)
    data = cursor.fetchall()
    data = data[-1][0]
    db.close()
    return data



def get_num_stock(moneyList, priceList):
    '''
    moneyList : array
    priceList : array
    '''    
    return moneyList / priceList


def get_basket_history(stockCodes, numStock, date_start, date_end):
    basketPriceData =  get_stock_price(stockCodes, date_start, date_end).fillna(0)
    dates = basketPriceData.index
    priceHistory = basketPriceData[stockCodes].values.dot(numStock)    
    priceHistory = pd.DataFrame(priceHistory, index = dates)
    return priceHistory
    
def get_equalweight(stockCode):   
    return np.ones(len(stockCode)) / len(stockCode)



####################################
#            Visualize  
####################################
#'''
#import matplotlib.pyplot as plt
#import matplotlib.dates as mdates
#import numpy as np
#plt.style.use('fivethirtyeight')
#
#date = cum_returnData.index.astype('O')
#close = cum_returnData[['BM', 'Fund', 'Fund_PBR']]
#fig, ax = plt.subplots(figsize = (10,8))
#fig.autofmt_xdate()
#ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')
#ax.plot(date, close, lw=2)
#plt.show()
#
## create two subplots with the shared x and y axes
#fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, sharey=False, figsize = (10, 8))
#ax1.plot(date, cum_returnData.BM, lw = 2, label = 'BM(KOSPI SmallCap)')
#ax1.plot(date, cum_returnData.Fund, lw = 2, label = 'Fund')
#ax2.fill_between(date, 0, cum_returnData['ER'], label = 'Excess Return', facecolor = 'blue', alpha = 0.5)
#for ax in ax1, ax2:
#    ax.grid(True)
#    ax.legend(fancybox=True, framealpha = 0.5, loc = 2)
#    
#fig.autofmt_xdate()
#plt.show()
#
#
