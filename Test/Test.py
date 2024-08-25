import os
import sys
import pandas as pd
import numpy as np
import backtrader as bt
import pyfolio as pf
from Paper.Paper import Paper
import matplotlib.pyplot as plt
from datetime import datetime

# Добавление пути к родительской директории
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class CustomSizer(bt.Sizer):
    params = (
        ('long_percent', 0.2),  # 20% от депозита для лонга
        ('short_percent', 0.3),  # 30% от депозита для шорта
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        price = data.close[0]
        if isbuy:
            size = (cash * self.p.long_percent) // price
        else:
            size = (cash * self.p.short_percent) // price
        return int(size)

class Strategy(bt.Strategy):
    params = (
        ('sl', 0.002),    # Стоп-лосс 0.2%
        ('tp', 0.005),    # Тейк-профит 0.5%
        ('window', 50),
    )

    def log(self, txt, dt=None):
        '''Функция логирования'''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.predict = self.datas[0].predict
        self.orders = []  # Список для отслеживания всех текущих ордеров
        self.buyprice = None
        self.buycomm = None

    def buy_order(self, price):
        size = self.getsizer()._getsizing(
            self.broker.getcommissioninfo(self.data),  # коммисионная информация
            self.broker.getcash(),  # текущие наличные средства
            self.data,  # данные
            isbuy=True  # это покупка
        )
        if size == 0:
            self.log(f"Buy order size is 0, not placing an order")
            return
        mainside = self.buy(
            price=price,
            exectype=bt.Order.Market,
            transmit=False
        )
        stop_price = price * (1.0 - self.params.sl)
        lowside = self.sell(
            size=mainside.size,    
            price=stop_price,
            exectype=bt.Order.Stop,
            transmit=False,
            parent=mainside
        )
        take_profit_price = price * (1.0 + self.params.tp)
        highside = self.sell(
            size=mainside.size,
            price=take_profit_price,
            exectype=bt.Order.Stop,
            transmit=True,
            parent=mainside
        )
        self.orders.extend([mainside, lowside, highside])

    def sell_order(self, price):
        size = self.getsizer()._getsizing(
            self.broker.getcommissioninfo(self.data),  # коммисионная информация
            self.broker.getcash(),  # текущие наличные средства
            self.data,  # данные
            isbuy=False  # это покупка
        )
        if size == 0:
            self.log(f"Sell order size is 0, not placing an order")
            return
        mainside = self.sell(
            price=price,
            exectype=bt.Order.Market,
            transmit=False
        )
        stop_price = price * (1.0 + self.params.sl)
        lowside = self.buy(
            size=mainside.size,
            price=stop_price,
            exectype=bt.Order.Stop,
            transmit=False,
            parent=mainside
        )
        take_profit_price = price * (1.0 - self.params.tp)
        highside = self.buy(
            size=mainside.size,
            price=take_profit_price,
            exectype=bt.Order.Stop,
            transmit=True,
            parent=mainside
        )
        self.orders.extend([mainside, lowside, highside])

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, Comm {order.executed.comm:.2f}'
                )
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        if order in self.orders:
            self.orders.remove(order)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def decide(self):
        '''
        Функция принятия решения:
        Возвращает:
            1  - сигнал на покупку (лонг)
            -1 - сигнал на продажу (шорт)
            0  - ничего не делать
        '''

        if len(self.predict) > 0:
            signal = self.predict[0]  # Предполагаем, что сигнал уже предсчитан и хранится в данных
            return signal
        return 0

    def next(self):
        # self.log(f'Close, {self.dataclose[0]:.2f}')
        if self.end_of_the_day():
            return
        decision = self.decide()
        if decision == 1:
            self.log(f'BUY CREATE, {self.dataclose[0]:.2f}')
            self.buy_order(self.dataclose[0])
        elif decision == -1:
            self.log(f'SELL CREATE, {self.dataclose[0]:.2f}')
            self.sell_order(self.dataclose[0])
        else:
            pass

    def end_of_the_day(self):
        current_time = self.datas[0].datetime.time(0)
        if current_time.hour == 23 and current_time.minute == 59:
            self.log(f'CLOSE ALL POSITIONS, {self.dataclose[0]:.2f}')
            self.close()
            return True
        return False

class Test:
    def __init__(self, paper, strategy=Strategy, tp=1, sl=0.5, balance=100_000, evening_session=False):
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
            lines = indicators_for_lines
            params = (
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
        cerebro.broker.setcommission(commission=0.0005)  # 0.05% комиссия
        cerebro.addstrategy(self.strategy)
        data = PandasData(dataname=self.paper.data)
        cerebro.adddata(data)
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        cerebro.addsizer(CustomSizer)
        print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
        self.results = cerebro.run()
        print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
        self.cerebro = cerebro

    def visualize(self):
        try:
            strat = self.results[0]
            pyfoliozer = strat.analyzers.getbyname('pyfolio')
            returns, positions, transactions = pyfoliozer.get_pf_items()
            pf.create_full_tear_sheet(
                returns,
                positions=positions,
                transactions=transactions,
                live_start_date='2018-01-03',  # Эта дата зависит от ваших данных
                round_trips=True
            )
        except Exception:
            self.cerebro.plot()


