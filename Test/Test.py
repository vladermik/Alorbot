import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Paper.Paper import Paper


class Test():
    def __init__(self, paper:Paper, tp:float=1, sl:float=0.5, balance:int=100_000, evening_session=False) -> None:
        self.paper = paper
        self.tp = tp
        self.sl = sl
        self.balance = balance
        self.history = []
        self.evening_session = evening_session
        self.positions = {}  # Словарь для хранения позиций: {цена: (количество, направление, стоп-лосс, тейк-профит)}

    def open_position(self, price, quantity, direction):
        stop_loss = price * (0.995 if direction == 'long' else 1.005)
        take_profit = price * (1.01 if direction == 'long' else 0.99)
        self.positions[price] = (quantity, direction, stop_loss, take_profit)
        print(f'{direction.capitalize()} position opened at {price} with {quantity} shares')

    def close_position(self, price, entry_price):
        quantity, direction, _, _ = self.positions[entry_price]
        if direction == 'long':
            self.balance += (price - entry_price) * quantity
        elif direction == 'short':
            self.balance += (entry_price - price) * quantity
        print(f'{direction.capitalize()} position closed at {price} with {quantity} shares')
        del self.positions[entry_price]
    
    def decide(self):
        '''
        :returns 
        1, amount if long
        0, 0 if do nothing
        -1, amount if short
        '''
        pass
    def emergency(self, price):
        print(11111)
        positions_to_close = list(self.positions.keys())
        for end_day_price in positions_to_close:
            self.close_position(price, end_day_price) 

    def run(self):
        for index, row in self.paper.data.iterrows():
            price = row['close']
            if (row['hour'] == 18 and row['minute'] == 39 and not self.evening_session) or \
            (row['hour'] == 23 and row['minute'] == 49 and self.evening_session):
                self.emergency(price)
                self.history.append(self.balance)
            else:     
                for entry_price in list(self.positions.keys()):
                    _, direction, stop_loss, take_profit = self.positions[entry_price]
                    if direction == 'long':
                        if price <= stop_loss:
                            print(f'Stop-loss triggered for long position at {price}')
                            self.close_position(price, entry_price)
                        elif price >= take_profit:
                            print(f'Take-profit triggered for long position at {price}')
                            self.close_position(price, entry_price)
                    elif direction == 'short':
                        if price >= stop_loss:
                            print(f'Stop-loss triggered for short position at {price}')
                            self.close_position(price, entry_price)
                        elif price <= take_profit:
                            print(f'Take-profit triggered for short position at {price}')
                            self.close_position(price, entry_price)
                direction, amount = self.decide(row)
                if direction == 1:
                    self.open_position(price, amount, 'long')
                elif direction == -1:
                    self.open_position(price, amount, 'short')