from yaml import load, CLoader as Loader
import os

path = os.path.join(
        os.path.abspath(os.path.join(__file__, os.pardir)),
        '../api_keys.yaml')

apikeys = load( open(path, 'rb'), Loader=Loader)


import yahoo_fin.stock_info as si

sp = si.tickers_sp500();

# Get Netflix Data
sample = si.get_data('nflx')
