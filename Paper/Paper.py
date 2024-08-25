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
        self.data['datetime'] = self.data['time'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
        self.data.drop('time', axis=1, inplace=True)
        self.data['datetime'] = pd.to_datetime(self.data['datetime'])
        self.data['hour'] = self.data['datetime'].dt.hour
        self.data['minute'] = self.data['datetime'].dt.minute

    def _mark(self, data_slice, sl, tp):
        sl_long, sl_short = sl
        tp_long, tp_short = tp
        l = len(data_slice) // 5

        lows = data_slice['low'].values
        highs = data_slice['high'].values

        for i in range(len(data_slice)):
            if lows[i] <= sl_long:
                break
            elif highs[i] >= tp_long:
                return 5 - int(i // l)

        for i in range(len(data_slice)):
            if highs[i] >= sl_short:
                break
            elif lows[i] <= tp_short:
                return -5 + int(i // l)
        
        return 0

    def mark(self, sl=0.5, tp=1, window=50):
        data_len = len(self.data)
        marks = np.full(data_len, None)
        for i in range(data_len - window):
            # print(f"{i} ... {data_len}")
            price = self.data.at[i, 'close']
            sls = (price * (1 - sl / 100), price * (1 + sl / 100))
            tps = (price * (1 + tp / 100), price * (1 - tp / 100))
            
            data_slice = self.data.iloc[i:i + window]
            if data_slice.loc[i, 'hour'] >= 15 and data_slice.loc[i, 'minute'] >= 39:
                mark = None
            else:
                mark = self._mark(data_slice, sls, tps)
            marks[i] = mark
        self.data['mark'] = marks
        self.indicators.append('mark')
        self.indicators.append('predict')

    def mark_report(self, sls=[0.2, 0.3], tps=[0.4, 0.6], window=50, save=True):
        report = {'tp': [], 'sl': [], 'rate': [], 'profit': []}
        for sl in sls:
            for tp in tps:
                self.mark(sl=sl, tp=tp, window=window)
                report['tp'].append(tp)
                report['sl'].append(sl)
                report['rate'].append(round(tp/sl, 2))
                profit = len(self.data[self.data['mark'] != 0]) * tp
                report['profit'].append(profit)
                self.data.drop('mark', axis=1, inplace=True)
                print(f"sl={sl}...tp={tp}")
        df = pd.DataFrame(report)
        if save:
            df.to_csv(rf'data/datasets/{self.ticker}/mark_report.csv')
        return df  

    def clear(self):
        return self.data.drop(['open', 'high', 'low', 'close', 'mark'], axis=1), self.data['mark']

    def change(self):
        self.data['change'] = (self.data['close'] - self.data['open']) / self.data['open']
    
    def ushadow(self):
        price = self.data[['open', 'close']].max(axis=1)
        self.data['ushadow'] = (self.data['high'] - price) / price

    def lshadow(self):
        price = self.data[['open', 'close']].min(axis=1)
        self.data['lshadow'] = (price - self.data['low']) / price

    def sma(self, duration=20):
        '''
        отклонение цены от sma
        '''
        sma = ta.trend.sma_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'sma{duration}'] = (self.data['close'] - sma) / sma * 100
        self.indicators.append(f'sma{duration}')

    def ema(self, duration=20):
        '''
        отклонение цены от ema
        '''
        ema = ta.trend.ema_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'ema{duration}'] = (self.data['close'] - ema) / ema * 100
        self.indicators.append(f'ema{duration}')

    def wma(self, duration=20):
        '''
        отклонение цены от wma
        '''
        wma = ta.trend.wma_indicator(close=self.data['close'],
                                    window=duration)
        self.data[f'wma{duration}'] = (self.data['close'] - wma) / wma * 100
        self.indicators.append(f'wma{duration}')

    def rsi(self, duration=14):
        rsi = ta.momentum.rsi(close=self.data['close'], 
                              window=duration)
        self.data[f'rsi{duration}'] = rsi
        self.indicators.append(f'rsi{duration}')

if __name__ == '__main__':
    paper = Paper("SBer", '1m')
    print(paper._get_params())