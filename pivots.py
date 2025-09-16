import yfinance as yf
from tests import download_data
import utils


pivotStrength = 2
trendStrength = 3

def get_pivots(data):
	pivots = []
	for i in range(len(data)-pivotStrength, ):
		high = data['High'].iloc[i]
		low = data['Low'].iloc[i] 
		pivotHigh = True
		pivotLow = True
		for j in range(-pivotStrength, pivotStrength):
			if (j == 0):
				continue
			if (data['High'].iloc[i+j] > high):
				pivotHigh = False
				break
			if (data['Low'].iloc[i+j] < low):
				pivotLow = False
				break

		# Pivot High
		if pivotHigh:
			pivots.append({'type': 'high', 'index': data.index[i], 'value': high})
		# Pivot Low
		if pivotLow:
			pivots.append({'type': 'low', 'index': data.index[i], 'value': low})
	
    # Devolver los últimos 3 pivots	
	return pivots[-3:]

#if __name__ == "__main__":
symbol = '6EZ25.CME'
start = '2025-07-29'
end = '2025-07-31'
interval = '1h'
data = utils.download_data(symbol, start, end, interval)

#print(data)

pivots = utils.pivots(data, pivotStrength, trendStrength)
print("pivots:", pivots)


'''pivots = get_pivots(data)
for pivot in pivots:
    print(f"Pivot {pivot['type']} at {pivot['index']}: {pivot['value']}")'''
	
utils.plot_candles_with_pivots(data, pivots, title=f'Candlestick with Pivots {symbol}')

#utils.plot_candles_with_pivots(data, pivots, title=f'Candlestick with Pivots {symbol}')

