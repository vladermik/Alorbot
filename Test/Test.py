import os
import sys
import pandas as pd
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Paper.Paper import Paper

class Test:
    def __init__(self, paper, tp=1, sl=0.5, balance=100_000, window=None, evening_session=False):
        self.paper = paper
        self.tp = tp
        self.sl = sl
        self.balance = balance
        self.history = []
        self.evening_session = evening_session
        self.window = window
        self.id = 0
        self.positions = pd.DataFrame(columns=['id', 'date', 'open', 'sl', 'tp', 'close', 'nshares', 'profit', 'direction'])
        self.opened_positions = pd.DataFrame(columns=['id', 'date', 'open', 'sl', 'tp', 'close', 'nshares', 'profit', 'direction'])

    def open_position(self, date, price, quantity, direction):
        sls = (price * (1 - self.sl / 100), price * (1 + self.sl / 100))
        tps = (price * (1 + self.tp / 100), price * (1 - self.tp / 100))
        stop_loss = sls[0] if direction == 'long' else sls[1]
        take_profit = tps[0] if direction == 'long' else tps[1]
        new_position = pd.DataFrame({'id': self.id, 'date': date, 'open': price, 'sl': stop_loss, 'tp': take_profit,
                        'close': None, 'nshares': quantity, 'profit': None, 'direction': direction}, index=[0])
        self.opened_positions = pd.concat([self.opened_positions, new_position], ignore_index=True)
        self.id += 1
        print(f'{direction.capitalize()} position opened at {price} with {quantity} shares')

    def close_position(self, price, pos_id):
        position = self.opened_positions.loc[self.opened_positions['id'] == pos_id].iloc[0]
        open_price = position['open']
        quantity = position['nshares']
        direction = position['direction']
        profit = (price - open_price) * quantity if direction == 'long' else (open_price - price) * quantity
        self.balance += profit
        self.opened_positions.loc[self.opened_positions['id'] == pos_id, 'profit'] = profit
        self.opened_positions.loc[self.opened_positions['id'] == pos_id, 'close'] = price
        self.positions = pd.concat([self.positions, self.opened_positions[self.opened_positions['id'] == pos_id]])
        self.opened_positions = self.opened_positions[self.opened_positions['id'] != pos_id]
        print(f'{direction.capitalize()} position closed at {price} with {quantity} shares')

    def check(self, price):
        conditions = (
            ((self.opened_positions['direction'] == 'long') & (price < self.opened_positions['sl'])) |
            ((self.opened_positions['direction'] == 'long') & (price > self.opened_positions['tp'])) |
            ((self.opened_positions['direction'] == 'short') & (price > self.opened_positions['sl'])) |
            ((self.opened_positions['direction'] == 'short') & (price < self.opened_positions['tp']))
        )
        ids = self.opened_positions.loc[conditions, 'id'].tolist()
        return ids if ids else None

    def decide(self):
        '''
        :returns 
        1, amount if long
        0, 0 if do nothing
        -1, amount if short
        '''
        pass

    def emergency(self, price):
        for pos_id in self.opened_positions['id']:
            self.close_position(price, pos_id)

    def run(self):
        for i in range(self.window, len(self.paper.data) - self.window):
            row = self.paper.data.iloc[i]
            price = row['close']
            high, low = row['high'], row['low']
            if (row['hour'] == 15 and row['minute'] == 39 and not self.evening_session) or \
                    (row['hour'] == 20 and row['minute'] == 49 and self.evening_session):
                print(f"end of {row['time'].date()}")
                self.emergency(price)
                self.history.append(self.balance)
            else:
                for pos_id in self.opened_positions['id']:
                    pos = self.opened_positions.loc[self.opened_positions['id'] == pos_id].iloc[0]
                    direction = pos['direction']
                    sl, tp = pos['sl'], pos['tp']
                    if ((direction == 'long' and low <= sl) or (direction == 'short' and low <= tp)):
                        print(f'{direction.capitalize()} position {"stop-loss" if direction == "long" else "take-profit"} triggered at {low}')
                        self.close_position(low, pos_id)
                    elif ((direction == 'long' and high >= tp) or (direction == 'short' and high <= sl)):
                        print(f'{direction.capitalize()} position {"stop-loss" if direction == "short" else "take-profit"} triggered at {high}')
                        self.close_position(high, pos_id)

                direction, amount = self.decide(self.paper.data.iloc[i - self.window:i])
                if direction == 1:
                    self.open_position(row['time'], price, amount, 'long')
                elif direction == -1:
                    self.open_position(row['time'], price, amount, 'short')