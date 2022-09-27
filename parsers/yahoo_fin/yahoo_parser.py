import yahoo_fin.stock_info as si

sp = si.tickers_sp500();

# Get Netflix Data
sample = si.get_data('nflx')
