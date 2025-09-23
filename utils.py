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
    pivots = classify_pivots(pivots)
    return pivots

def classify_pivots(pivots):
    """
    Recorre el arreglo de pivots de la vela más antigua a la más reciente y clasifica:
    - Para 'high':
        - Si el high es mayor al pivot high anterior: 'HH'
        - Si es menor: 'LH'
    - Para 'low':
        - Si el low es menor al pivot low anterior: 'LL'
        - Si es mayor: 'HL'
    El resultado se guarda en la clave 'type2' de cada diccionario de pivot.
    """
    last_high = None
    last_low = None
    for pivot in pivots:
        if pivot['type'] == 'high':
            if last_high is None:
                pivot['type2'] = ''
            else:
                if pivot['value'] > last_high:
                    pivot['type2'] = 'HH'
                else:
                    pivot['type2'] = 'LH'
            last_high = pivot['value']
        elif pivot['type'] == 'low':
            if last_low is None:
                pivot['type2'] = ''
            else:
                if pivot['value'] < last_low:
                    pivot['type2'] = 'LL'
                else:
                    pivot['type2'] = 'HL'
            last_low = pivot['value']
    return pivots

def plot(data, ticker):
    mpf.plot(data, 
             type='candle', 
             style='charles', 
             title='Futuro del ' + ticker, 
             volume=False, figratio=(24,8)) 
    plt.show()

def get_trend(pivots, trendStrength):
    # Determina la tendencia basada en los últimos pivotes.

    # Si hay menos pivotes que trendStrength, no hay tendencia definida.
    if len(pivots) < trendStrength:
        return 'No trend'
    
    #Para tendecial bullish, la condicion es que sea una secuencia de HH y HL
    trend = 'up'
    for pivot in pivots[-trendStrength:]:
        if pivot['type2'] == 'HH' or pivot['type2'] == 'HL':
            continue
        else:
            return 'No trend'
        
    #Para tendecial bearish, la condicion es que sea una secuencia de LL y LH
    trend = 'down'
    for pivot in pivots[-trendStrength:]:
        if pivot['type2'] == 'LL' or pivot['type2'] == 'LH':
            continue
        else:
            return 'No trend'
    
    return trend




def plot_candles_with_pivots(data, pivots, title='Candlestick with Pivots'):
    data = data.copy()
    data.index = pd.to_datetime(data.index)
    high_marker = [np.nan] * len(data)
    low_marker = [np.nan] * len(data)
    high_text = [''] * len(data)
    low_text = [''] * len(data)
    idx_map = {idx: i for i, idx in enumerate(data.index)}
    for pivot in pivots:
        i = idx_map.get(pivot['index'])
        if i is not None:
            label = pivot.get('type2', '')
            if pivot['type'] == 'high':
                high_marker[i] = pivot['value']
                high_text[i] = label
            elif pivot['type'] == 'low':
                low_marker[i] = pivot['value']
                low_text[i] = label
    apds = [
        mpf.make_addplot(high_marker, type='scatter', markersize=0, color='r'),
        mpf.make_addplot(low_marker, type='scatter', markersize=0, color='b')
    ]
    fig, axes = mpf.plot(
        data,
        type='candle',
        addplot=apds,
        style='charles',
        title=title,
        ylabel='Precio',
        returnfig=True
    )
    ax = axes[0]
    for i, txt in enumerate(high_text):
        if txt:
            ax.text(i, high_marker[i], txt, color='red', fontsize=14, ha='center', va='bottom', fontweight='bold')
    for i, txt in enumerate(low_text):
        if txt:
            ax.text(i, low_marker[i], txt, color='blue', fontsize=14, ha='center', va='top', fontweight='bold')
    
    # Mostrar la tendencia en la gráfica
    trend = get_trend(pivots, trendStrength=3)  # Puedes ajustar trendStrength si lo deseas
    ax.text(0.01, 0.98, f'Tendencia: {trend}', transform=ax.transAxes, fontsize=16, color='purple',
            ha='left', va='top', bbox=dict(facecolor='white', alpha=0.7, edgecolor='purple'))
    plt.show()