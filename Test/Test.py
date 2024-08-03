import os
import sys
import pandas as pd
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backtrader as bt
import pyfolio as pf
from Paper.Paper import Paper
import matplotlib.pyplot as plt
class PandasData(bt.feeds.PandasData):
        lines = ('rsi14',)
        params = (
        ('datetime', None),  # Убедитесь, что 'time' является индексом времени
        ('close', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('volume', 4),
        ('hour', 5),
        ('minute', 6),
        ('rsi14', 7),  # Индекс для rsi14
        # ('ema20', 'ema20'),
        # ('ema50', 'ema50'),
        # ('ema100', 'ema100'),
        # ('ema200', 'ema200'),
    )
class Strategy(bt.Strategy):
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.rsi = self.datas[0].rsi14
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close
                    if self.dataclose[-1] < self.dataclose[-2]:
                        self.log(f'RSI .................. {list(self.datas[0])}')
                        # previous close less than the previous close
                        # BUY, BUY, BUY!!! (with default parameters)
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])
                        # Keep track of the created order to avoid a 2nd order
                        self.order = self.buy()
        else:
            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
    
class Test():
    def __init__(self, paper, strategy=None, tp=1, sl=0.5, balance=100_000, evening_session=False):
        self.tp = tp / 100
        self.sl = sl / 100
        self.balance = balance
        self.evening = evening_session
        self.strategy = strategy
        self.paper = paper

    def run(self):
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(self.balance)
        cerebro.broker.setcommission(commission=0.0005)  # 0.1% комиссия
        cerebro.addstrategy(self.strategy)
        data = PandasData(dataname=self.paper.data)
        cerebro.adddata(data)
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        self.results = cerebro.run()
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
        self.cerebro = cerebro
        cerebro.plot()


    def visualize(self):
        try:
            strat = self.results[0]
            pyfoliozer = strat.analyzers.getbyname('pyfolio')
            returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
            print(returns.head())
            print(positions.head())
            print(transactions.head())
            # pyfolio showtime
            pf.create_full_tear_sheet(
                returns,
                positions=positions,
                transactions=transactions,
                gross_lev=gross_lev,
                live_start_date='2018-01-03',  # This date is sample specific
                round_trips=True)
            plt.show()
        except Exception:
            self.cerebro.plot()
            plt.show()



