import requests
import settings as s
import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils
import time

class Alor():
    def __init__(self, exchange='MOEX'):
        self.exchange = exchange
        self.refresh_token = s.REFRESH_TOKEN
        self.jwt_token = self._get_jwt_token()
        self.auth_header = {'Authorization': f'Bearer {self.jwt_token}'}
    
    def _get_jwt_token(self):
        payload = {'token': self.refresh_token}
        url = f"{s.URL_OAUTH}/refresh"
        res = requests.post(url, params=payload)
        if res.status_code != 200:
            if s.LOGGING:
                pass
            raise Exception(f"Ошибка при получении JWT токена: {res.status_code}")
        return res.json().get('AccessToken')
    
    def get_all_instruments(self, data_dir='data/info_about_instruments', _format='Heavy', _market='FOND'):
        payload = {'exchange': self.exchange,
                   'format': _format,
                   'market': _market,
                   'includeOld': False
                   }
        url = s.URL_API + s.INSTRUMENTS_URL + self.exchange
        res = requests.get(url, headers=self.auth_header, params=payload)
        if res.status_code != 200:
            print('error')
            return
        res_j = res.json()
        df = pd.DataFrame(res_j)
        if data_dir:
            data_dir = f'{data_dir}/all_instruments.csv'
            try:
                df.to_csv(data_dir, index=False)
            except PermissionError as e:
                print(f"Ошибка доступа: {e}")
                utils.set_permissions(data_dir)
                try:
                    df.to_csv(data_dir, index=False)
                except Exception as e:
                    print(f"Повторно произошла ошибка: {e}")
            except Exception as e:
                print(f"Произошла ошибка: {e}")

    def get_instrument_info(self, ticker:str):
        ticker = ticker.upper()
        df = pd.read_csv(r"data\info_about_instruments\all_instruments.csv")
        df = df[df['symbol'] == ticker]
        df.set_index('symbol', inplace=True)
        df.to_dict(orient='index')
        return df.to_dict(orient='index')[ticker]
    
    def get_history(ticker, start=1514754000, end=int(time.time())):
        '''
        start - unix timestamp, default=2018/01/01 00:00:00
        end - inux timestamp, default=now
        
        :returns 
        '''
        pass

alor = Alor()
print(alor.get_instrument_info("SBER"))
        