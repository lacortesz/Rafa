def plot_candles_matplotlib(data, title='Candlestick Chart'):
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    data = data.copy()
    data.index = pd.to_datetime(data.index)
    fig, ax = plt.subplots(figsize=(12, 6))
    width = 0.6
    width2 = 0.1
    dates = mdates.date2num(data.index.to_pydatetime())
    for idx, (date, row) in enumerate(data.iterrows()):
        open_, high, low, close = row['Open'], row['High'], row['Low'], row['Close']
        color = 'green' if close >= open_ else 'red'
        # Cuerpo de la vela
        rect = Rectangle((dates[idx] - width/2, min(open_, close)), width, abs(close - open_), color=color, alpha=0.8)
        ax.add_patch(rect)
        # Mechas
        ax.plot([dates[idx], dates[idx]], [low, high], color='black', linewidth=1)
    ax.xaxis_date()
    ax.set_title(title)
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Precio')
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt

def download_data(ticker, start, end, interval):
    
    # Downloads historical market data for a given ticker symbol.
    df = yf.download(ticker, start=start, end=end, interval=interval, multi_level_index=False)
    if df.empty:
        raise ValueError(f"No data fetched for {ticker}. Check ticker or date range.")
    return df

def pivots(data, pivotStrength, trendStrength):
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

def plot_candles(data, title='Candlestick Chart'):
    data = data.copy()
    data.index = pd.to_datetime(data.index)
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candles')])
    fig.update_layout(title=title, xaxis_title='Fecha', yaxis_title='Precio', xaxis_rangeslider_visible=True)
    fig.show()

def plot_candles_with_pivots(data, pivots, title='Candlestick with Pivots'):
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
    '''for pivot in pivots:
        color = 'red' if pivot['type'] == 'high' else 'blue'
        symbol = 'triangle-up' if pivot['type'] == 'high' else 'triangle-down'
        fig.add_trace(go.Scatter(
            x=[pivot['index']],
            y=[pivot['value']],
            mode='markers',
            marker=dict(color=color, size=12, symbol=symbol),
            name=f"Pivot {pivot['type']}"
        ))'''
    fig.update_layout(title=title, xaxis_title='Fecha', yaxis_title='Precio', xaxis_rangeslider_visible=True)
    fig.show()