from yaml import load, CLoader as Loader
import os

path = os.path.abspath(os.path.join(__file__, os.pardir))

apikeys = load( open(os.path.join(path,'../api_keys.yaml'),
                    'rb'), Loader=Loader)

data_dir = os.path.join(path, 'yahoo_stock_prices')

import time


import yahoo_fin.stock_info as si
from tqdm.auto import tqdm
import pandas as pd
 

class Yahoo_Parser:
    
    # Name of stock ticker set that has been previously looked up on api
    known_name = 'known_tickers.txt'

    def __init__(self, data_dir):
        self.data_dir = data_dir;


        self.known = None;
        if os.path.exists(os.path.join(self.data_dir, self.known_name)):
            self.load_known();
        else:
            self.known = set();

    # Get Stock Price
    def get_sp(self, ticker):
        if ticker in self.known:
            return self.load_sp(ticker);

        print("Unknown ticker! Requesting from Server")
        
        sp = si.get_data(ticker.lower())
        self.save_sp(sp, ticker);
        self.known = self.known.union(set([ticker]))
        self.save_known();
        
        return sp;

    def load_sp(self, ticker):
        path = os.path.join(self.data_dir, f"{ticker}.pkl")
        return pd.read_pickle(path)

    def save_sp(self, sp, ticker):
        path = os.path.join(self.data_dir, f"{ticker.lower()}.pkl")
        sp.to_pickle(path)

    def save_known(self):
        if len(self.known) == 0:
            return;
        path = os.path.join(self.data_dir, self.known_name)
        with open(path, 'w') as f:
            tickers = list(self.known)
            f.write(tickers[0])
            for ticker in tickers[1:]:
                f.write(f"\n{ticker}")

    def load_known(self):
        path = os.path.join(self.data_dir, self.known_name)
        self.known = set(open(path, 'r').read().strip().split('\n'))

sp = si.tickers_sp500();
tickers = [i.split(',')[0] for i in open(os.path.join(path, 'tickers.txt'),'r').read().strip().split('\\n')]

# Get Netflix Data
sample = si.get_data('nflx')
s = sample

finans = si.get_financials('nflx')
f = finans

parser = Yahoo_Parser(data_dir);
for i in tqdm(sp):
    data.append([i, parser.get_sp(i.lower())])
