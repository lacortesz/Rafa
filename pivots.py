import yfinance as yf
from tests import download_data
import utils


pivotStrength = 2
trendStrength = 3



#if __name__ == "__main__":
symbol = '6EZ25.CME'
start = '2025-07-29'
end = '2025-07-31'
interval = '1h'
data = utils.download_data(symbol, start, end, interval)

#print(data)

pivots = utils.get_pivots(data, pivotStrength, trendStrength)
print("pivots:", pivots)

#utils.plot(data, symbol)
utils.plot_candles_with_pivots_mpf(data, pivots, title=f'Candlestick with Pivots {symbol}')

#utils.plot_candles(data, title=f'Candlestick with Pivots {symbol}')

'''pivots = get_pivots(data)
for pivot in pivots:
    print(f"Pivot {pivot['type']} at {pivot['index']}: {pivot['value']}")'''
	


#utils.plot_candles_with_pivots(data, pivots, title=f'Candlestick with Pivots {symbol}')

