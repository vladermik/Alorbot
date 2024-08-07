import os
import sys
import pandas as pd
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import backtrader as bt
import pyfolio as pf
from Paper.Paper import Paper
import matplotlib.pyplot as plt
# class PandasData(bt.feeds.PandasData):
#         lines = ('rsi14',)
#         params = (
#         ('datetime', None),  # Убедитесь, что 'time' является индексом времени
#         ('close', 0),
#         ('open', 1),
#         ('high', 2),
#         ('low', 3),
#         ('volume', 4),
#         ('hour', 5),
#         ('minute', 6),
#         ('rsi14', 7),  # Индекс для rsi14
#         # ('ema20', 'ema20'),
#         # ('ema50', 'ema50'),
#         # ('ema100', 'ema100'),
#         # ('ema200', 'ema200'),
#     )
class Strategy(bt.Strategy):
    params = (
        ('order_size', 100),
        ('sl', 0.002),
        ('tp', 0.005),
        ('window', 50)
    )
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.predict = self.datas[0].predict
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def buy_order(self, price):
        mainside = self.buy(
            price=price,
            size=self.params.order_size,
            exectype=bt.Order.Market,
            transmit=False
        )
        stop_price = price * (1.0 - self.params.sl)
        lowside = self.sell(
            price=stop_price,
            size=self.params.order_size,
            exectype=bt.Order.Stop,
            transmit=False,
            parent=mainside
        )
        take_profit_price = price * (1.0 + self.params.tp)
        highside = self.sell(
            price=take_profit_price,
            size=self.params.order_size,
            exectype=bt.Order.Limit,
            transmit=True,
            parent=mainside
        )
        self.order = mainside

    def sell_order(self, price):
        mainside = self.sell(
            price=price,
            size=self.params.order_size,
            exectype=bt.Order.Market,
            transmit=False
        )
        stop_price = price * (1.0 + self.params.sl)
        lowside = self.buy(
            price=stop_price,
            size=self.params.order_size,
            exectype=bt.Order.Stop,
            transmit=False,
            parent=mainside
        )
        take_profit_price = price * (1.0 - self.params.tp)
        highside = self.buy(
            price=take_profit_price,
            size=self.params.order_size,
            exectype=bt.Order.Limit,
            transmit=True,
            parent=mainside
        )
        self.order = mainside

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
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
    def decide(self):
        '''
        1 - buy
        0 - nothing to do
        -1 - sell
        '''
        prediction = model.predict(input_data)
        signal = np.argmax(prediction, axis=1)[0]  # Assuming the model returns probabilities for each class


    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        if self.end_of_the_day():
            return
        if self.order:
            return

        desicion = self.decide()
        if desicion == 1:
            self.log('BUY CREATE, %.2f' % self.dataclose[0])
            self.order = self.buy_order(self.dataclose[0])
        elif desicion == -1:
            self.log('SELL CREATE, %.2f' % self.dataclose[0])
            self.order = self.sell_order(self.dataclose[0])
        else:
            pass

    def end_of_the_day(self):
        current_time = self.datas[0].datetime.time(0)
        if current_time.hour == 23 and current_time.minute == 59:
            self.log('CLOSE ALL POSITIONS, %.2f' % self.dataclose[0])
            self.close()
            return 1
        return 0
    
class Test():
    def __init__(self, paper, strategy=None, tp=1, sl=0.5, balance=100_000, evening_session=False):
        self.tp = tp / 100
        self.sl = sl / 100
        self.balance = balance
        self.evening = evening_session
        self.strategy = strategy
        self.paper = paper

    def run(self):
        indicators = self.paper.indicators
        indicators_for_lines = tuple(indicators)
        indicators_for_params = tuple((indicators[i], -1) for i in range(len(indicators)))
        class PandasData(bt.feeds.PandasData):
            '''
            1
            '''
            lines = indicators_for_lines
            params =(      
            ('datetime', None),
            ('close', 0),
            ('open', 1),
            ('high', 2),
            ('low', 3),
            ('volume', -1),
            ('hour', -1),
            ('minute', -1),
            ) + indicators_for_params
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
        # cerebro.plot()


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



