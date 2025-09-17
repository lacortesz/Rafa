import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np

def download_data(ticker, start, end, interval):
    
    # Downloads historical market data for a given ticker symbol.
    df = yf.download(ticker, start=start, end=end, interval=interval, multi_level_index=False)
    if df.empty:
        raise ValueError(f"No data fetched for {ticker}. Check ticker or date range.")
    return df

def get_pivots(data, pivotStrength, trendStrength):
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

		# Pivot High
		if pivotHigh:
			pivots.append({'type': 'high', 'index': data.index[i], 'value': high})

		for j in range(-pivotStrength, pivotStrength):
			if (j == 0):
				continue
			if (data['Low'].iloc[i+j] < low):
				pivotLow = False
				break
		
		# Pivot Low
		if pivotLow:
			pivots.append({'type': 'low', 'index': data.index[i], 'value': low})
	
    # Devolver los últimos 3 pivots	
	return clean_pivots(pivots, pivotStrength)

def clean_pivots(pivots, pivotStrength):
    i = 0
    while i < len(pivots)-1:
    #for i in range(0, 42, 1):
        print('Pivot ' + str(i) + ' de: '  + str(len(pivots)) + ' info ' + str(pivots[i]))
        if pivots[i]['type'] == 'high':
            if pivots[i+1]['type'] == 'high':
                if pivots[i+1]['value'] > pivots[i]['value']:
                    print('Elimino pivot high ' + str(pivots[i]))
                    pivots.remove(pivots[i])
                else:
                    print('Elimino pivot high ' + str(pivots[i+1]))
                    pivots.remove(pivots[i+1])
                i = 0
        if pivots[i]['type'] == 'low':
            if pivots[i+1]['type'] == 'low':
                if pivots[i+1]['value'] < pivots[i]['value']:
                    print('Elimino pivot low ' + str(pivots[i]))
                    pivots.remove(pivots[i])
                else:
                    print('Elimino pivot low ' + str(pivots[i+1]))
                    pivots.remove(pivots[i+1])
                i = 0
        i += 1
    return pivots


def plot(data, ticker):
    mpf.plot(data, 
             type='candle', 
             style='charles', 
             title='Futuro del ' + ticker, 
             volume=False, figratio=(24,8)) 
    plt.show()

def plot_candles_with_pivots(data, pivots, title='Candlestick with Pivots'):
    data = data.copy()
    data.index = pd.to_datetime(data.index)
    high_marker = [np.nan] * len(data)
    low_marker = [np.nan] * len(data)
    idx_map = {idx: i for i, idx in enumerate(data.index)}
    for pivot in pivots:
        i = idx_map.get(pivot['index'])
        if i is not None:
            if pivot['type'] == 'high':
                high_marker[i] = pivot['value']
            elif pivot['type'] == 'low':
                low_marker[i] = pivot['value']
    apds = [
        mpf.make_addplot(high_marker, type='scatter', markersize=100, marker='^', color='r'),
        mpf.make_addplot(low_marker, type='scatter', markersize=100, marker='v', color='b')
    ]
    mpf.plot(
        data,
        type='candle',
        addplot=apds,
        style='charles',
        title=title,
        ylabel='Precio'
    )