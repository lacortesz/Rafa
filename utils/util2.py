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

def pivots_(data, pivotStrength, trendStrength):
    #data = data.copy()
    #data.index = pd.to_datetime(data.index)
    pivots = []
    for i in range(len(data) - trendStrength, trendStrength,-1):
        high = data['High'].iloc[i]
        low = data['Low'].iloc[i]
        print('Counter' + str(i) + ' High: ' + str(high) + ', Low: ' + str(low))

        if high > data['High'].iloc[i-1] and high > data['High'].iloc[i-2] and high > data['High'].iloc[i-3]:
            #print('Pivot High at index ' + str(data.index[i]) + ' with value ' + str(high))
            #return [{'type': 'high', 'index': data.index[i], 'value': high}]
            pivots.append({'type': 'high', 'index': data.index[i], 'value': high})
        if low < data['Low'].iloc[i-1] and low < data['Low'].iloc[i-2] and low < data['Low'].iloc[i-3]:
            #print('Pivot Low at index ' + str(data.index[i]) + ' with value ' + str(low))
            #return [{'type': 'low', 'index': data.index[i], 'value': low}]
            pivots.append({'type': 'low', 'index': data.index[i], 'value': low})

    return pivots

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
	return pivots


def clean_pivots(pivots, pivotStrength):
    for i in range(0, len(pivots)-1):
        if pivots[i+1]['type'] == 'high':
            if pivots[i]['type'] == 'high':
                if pivots[i]['value'] > pivots[i+1]['value']:
                    print('Elimino pivot high ' + str(pivots[i+1]))
                    pivots.remove(pivots[i+1])
                else:
                    print('Elimino pivot high ' + str(pivots[i]))
                    pivots.remove(pivots[i])
        if pivots[i+1]['type'] == 'low':
            if pivots[i]['type'] == 'low':
                if pivots[i]['value'] < pivots[i+1]['value']:
                    print('Elimino pivot low ' + str(pivots[i+1]))
                    pivots.remove(pivots[i+1])
                else:
                    print('Elimino pivot low ' + str(pivots[i]))
                    pivots.remove(pivots[i])
    return pivots

'''def plot_candles_with_pivots(data, pivots, title='Candlestick with Pivots'):
    data = data.copy()
    data.index = pd.to_datetime(data.index)
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candles')])
    # Agregar los pivots
    for pivot in pivots:
        color = 'red' if pivot['type'] == 'high' else 'blue'
        symbol = 'triangle-up' if pivot['type'] == 'high' else 'triangle-down'
        fig.add_trace(go.Scatter(
            x=[pivot['index']],
            y=[pivot['value']],
            mode='markers',
            marker=dict(color=color, size=12, symbol=symbol),
            name=f"Pivot {pivot['type']}"
        ))
    fig.update_layout(title=title, xaxis_title='Fecha', yaxis_title='Precio', xaxis_rangeslider_visible=True)
    fig.show() '''

def plot(data, ticker):
    mpf.plot(data, 
             type='candle', 
             style='charles', 
             title='Futuro del ' + ticker, 
             volume=False, figratio=(24,8)) 
    plt.show()

def plot_candles_with_pivots(data, pivots, title='Candlestick with Pivots'):
    apds = []
    for pivot in pivots:
        color = 'r' if pivot['type'] == 'high' else 'b'
        marker = '^' if pivot['type'] == 'high' else 'v'
        apds.append(
            mpf.make_addplot(
                [pivot['value'] if idx == pivot['index'] else None for idx in data.index],
                type='scatter', markersize=100, marker=marker, color=color
            )
        )
    mpf.plot(data, 
             type='candle',
            addplot=apds,
            style='charles',
            title='Candlestick with Pivots',
            ylabel='Precio')
    plt.show()

def plot_candles_with_pivots_mpf(data, pivots, title='Candlestick with Pivots'):
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