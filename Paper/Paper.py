import pandas as pd
import numpy as np
import ta
import os
import sys
from datetime import datetime

import ta.momentum
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import AlorApiWrapper.AlorApi as aa

class Paper():
    def __init__(self, ticker, timeframe='1m') -> None:
        path_dir = f"data/datasets/{ticker.upper()}"
        path = f"{path_dir}/{timeframe}.csv"
        if os.path.exists(path_dir) and os.path.isfile(path):
            self.data = pd.read_csv(path)
        else:
            self.data = aa.AlorApi().get_history(ticker=ticker, timeframe=timeframe)
        self.indicators = []
        self.ticker = ticker.upper()
        self._get_params()

    def _get_params(self):
        df = pd.read_csv(r"data\info_about_instruments\all_instruments.csv")
        df = df[df['symbol'] == self.ticker]
        self.shortName = df['shortName']
        self.step = df['minStep']
        self.roundTo = df['roundTo']
        self.marginBuy = df['marginBuy']
        self.marginSell = df['marginSell']
        self.lotSize = df['lotSize']

    def convert_date(self):
        self.data['time'] = self.data['time'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
        self.data['time'] = pd.to_datetime(self.data['time'])
    
    def sma(self, duration=20):
        '''
        отклонение цены от sma
        '''
        sma = ta.trend.sma_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'sma{duration}'] = (self.data['close'] - sma) / sma * 100

    def ema(self, duration=20):
        '''
        отклонение цены от ema
        '''
        ema = ta.trend.ema_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'ema{duration}'] = (self.data['close'] - ema) / ema * 100
    def wma(self, duration=20):
        '''
        отклонение цены от wma
        '''
        wma = ta.trend.wma_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'wma{duration}'] = (self.data['close'] - wma) / wma * 100
        
    def rsi(self, duration=14):
        rsi = ta.momentum.rsi(close=self.data['close'], 
                              window=duration)
        self.data[f'rsi{duration}'] = rsi
        
paper = Paper("SBer", '1m')
print(paper._get_params())