import requests
import os
import sys
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import AlorApiWrapper.settings as s
import time

class AlorApi():
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
        url = s.URL_API + '/md/v2/Securities/' + self.exchange
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

    def _get_instrument_info(self, ticker:str):
        ticker = ticker.upper()
        df = pd.read_csv(r"data\info_about_instruments\all_instruments.csv")
        df = df[df['symbol'] == ticker]
        df.set_index('symbol', inplace=True)
        df.to_dict(orient='index')
        return df.to_dict(orient='index')[ticker]
    
    def get_history(self, ticker, timeframe=60, start=1514754000, end=int(time.time()), save=False):
        '''
        timeframe - Длительность таймфрейма. В качестве значения можно указать точное количество секунд или код таймфрейма:
            15 — 15 секунд
            60 — 60 секунд или 1 минута
            3600 — 3600 секунд или 1 час
            D — сутки (соответствует значению 86400)
            W — неделя (соответствует значению 604800)
            M — месяц (соответствует значению 2592000)
            Y — год (соответствует значению 31536000)
        start - unix timestamp, default=2018/01/01 00:00:00
        end - inux timestamp, default=now
        
        :returns 
        if save = True 
            None
        else
            pd.Dataframe
        '''
        data_dir = r'data/datasets' #----------------------------------------------------------------------------------
        url = s.URL_API + '/md/v2/history' 
        payload = {'symbol': ticker,
                   'exchange': self.exchange,
                   'tf': timeframe,
                   'from': start,
                   'to': end}
        res = requests.get(url, headers=self.auth_header, params=payload)
        if res.status_code == 200:
            print("its ok")
        df = pd.DataFrame(res.json()['history'])
        if not save:
            return df
        if isinstance(timeframe, str):
            name = timeframe.lower()
        else:
            if timeframe < 60:
                name = f'{timeframe}s'
            elif 60 <= timeframe < 3600:
                name = f'{timeframe//60}m'
            else:
                name = f'{timeframe//3600}h'
        path = data_dir + '/' + ticker
        if not os.path.exists(path):
            os.makedirs(path)
        df.to_csv(f'{path}/{name}.csv', index=False)
        
if __name__ == "__main__":
    df = pd.read_csv(r"data/info_about_instruments/all_instruments.csv")
    lst = df[(df['primaryBoard'] == 'TQBR') & (df['type'].isin(['CS', 'PS', 'RDR']))]['symbol'].tolist()
    alor = AlorApi()
    for ticker in lst:
        alor.get_history(ticker=ticker, timeframe=60, save=True)
        print(f'{ticker} is done')
    alor.get_instrument_info()