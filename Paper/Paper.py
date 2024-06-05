import pandas as pd
import numpy as np
import ta
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import AlorApiWrapper.AlorApi as aa

class Paper():
    def __init__(self, ticker, timeframe='1m') -> None:
        path_dir = f"data/datasets/{ticker.upper()}"
        path = f"{path_dir}/{timeframe}.csv"
        print(path, path_dir)
        if os.path.exists(path_dir) and os.path.isfile(path):
            self.data = pd.read_csv(path)
        else:
            self.data = aa.AlorApi().get_history(ticker=ticker, timeframe=timeframe)
        self.indicators = []
    
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
        отклонение цены от sma
        '''
        wma = ta.trend.wma_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'wma{duration}'] = (self.data['close'] - wma) / wma * 100
        
paper = Paper("SBer", '1m')
print(paper.sma())