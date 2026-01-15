import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
from scipy.signal import argrelextrema
import plotly.io as pio
import webbrowser
import tempfile
import os
import ta
import empyrical as ep
from pathlib import Path
import threading
import utility.parameters as parameters
from sqlalchemy import create_engine, text


def download_data(ticker, start, end, interval):
    
    # Downloads historical market data for a given ticker symbol.
    df = yf.download(ticker, start=start, end=end, interval=interval, multi_level_index=False)
    if df.empty:
        raise ValueError(f"No data fetched for {ticker}. Check ticker or date range.")
    return df

def get_pivots(data, pivotStrength, trendStrength):
	pivots = []
	for i in range(len(data)-pivotStrength, ):
		high = data['high'].iloc[i]
		low = data['low'].iloc[i] 
		pivotHigh = True
		pivotLow = True
		for j in range(-pivotStrength, pivotStrength):
			if (j == 0):
				continue
			if (data['high'].iloc[i+j] > high):
				pivotHigh = False
				break

		# Pivot High
		if pivotHigh:
			pivots.append({'type': 'high', 'index': data.index[i], 'value': high})

		for j in range(-pivotStrength, pivotStrength):
			if (j == 0):
				continue
			if (data['low'].iloc[i+j] < low):
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


    ## --------------------------11/10/2025 -------------------

def identificar_pivots(df, n=2):
    """
    Identifica pivots en un DataFrame de precios OHLC.
    Parámetros:
        df (pd.DataFrame): debe contener columnas ['high', 'low']
        n (int): número de velas a cada lado para confirmar un pivot
    Retorna:
        pd.DataFrame con columnas adicionales:
        'pivot_high', 'pivot_low', 'pivot_label'
    """
    df = df.copy()
    df['pivot_high'] = False
    df['pivot_low'] = False
    df['pivot_label'] = None

    for i in range(n, len(df) - n):
        # Pivot High
        if df['high'].iloc[i] == max(df['high'].iloc[i - n:i + n + 1]):
            df.loc[df.index[i], 'pivot_high'] = True

        # Pivot Low
        if df['low'].iloc[i] == min(df['low'].iloc[i - n:i + n + 1]):
            df.loc[df.index[i], 'pivot_low'] = True

    # Clasificar pivots como HH, LH, HL, LL
    last_high = None
    last_low = None

    for i in range(len(df)):
        if df['pivot_high'].iloc[i]:
            if last_high is not None:
                label = "HH" if df['high'].iloc[i] > last_high else "LH"
            else:
                label = "H"
            df.loc[df.index[i], 'pivot_label'] = label
            last_high = df['high'].iloc[i]

        elif df['pivot_low'].iloc[i]:
            if last_low is not None:
                label = "HL" if df['low'].iloc[i] > last_low else "LL"
            else:
                label = "L"
            df.loc[df.index[i], 'pivot_label'] = label
            last_low = df['low'].iloc[i]

    return limpiar_pivots(df)

def limpiar_pivots(df):
    """
    Elimina pivots redundantes:
    - Si hay dos pivots High seguidos, deja solo el mayor.
    - Si hay dos pivots Low seguidos, deja solo el menor.
    - Si hay dos pivots en la misma fecha, prioriza el High.
    """
    df = df.copy()

    # Extraer solo filas con pivots
    pivots = df[(df['pivot_high']) | (df['pivot_low'])].copy()
    pivots['tipo'] = np.where(pivots['pivot_high'], 'H', 'L')

    indices_a_eliminar = []

    # Regla 1 y 2: eliminar pivots consecutivos del mismo tipo
    for i in range(1, len(pivots)):
        prev_idx = pivots.index[i - 1]
        curr_idx = pivots.index[i]

        if pivots['tipo'].iloc[i] == pivots['tipo'].iloc[i - 1]:
            if pivots['tipo'].iloc[i] == 'H':
                # Dejar solo el más alto
                if pivots['high'].iloc[i] > pivots['high'].iloc[i - 1]:
                    indices_a_eliminar.append(prev_idx)
                else:
                    indices_a_eliminar.append(curr_idx)
            else:
                # Dejar solo el más bajo
                if pivots['low'].iloc[i] < pivots['low'].iloc[i - 1]:
                    indices_a_eliminar.append(prev_idx)
                else:
                    indices_a_eliminar.append(curr_idx)

        # Regla 3: pivots en la misma fecha
        if prev_idx == curr_idx:
            if pivots['tipo'].iloc[i] == 'L':
                indices_a_eliminar.append(curr_idx)

    # Eliminar los índices marcados
    df.loc[indices_a_eliminar, ['pivot_high', 'pivot_low', 'pivot_label']] = [False, False, None]

    return df

def determinar_tendencia(df, n=3):
    """
    Determina la tendencia basada en los últimos 3 pivots (H/L).
    Reglas:
      - Si últimos 3 pivots son: Low -> High -> Low mayor → Bullish
      - Si últimos 3 pivots son: High -> Low -> High menor → Bearish
      - En cualquier otro caso → Sin tendencia
    """
    pivots = df[df['pivot_label'].notnull()][['pivot_high', 'pivot_low', 'pivot_label', 'high', 'low']]

    if len(pivots) < n:
        return "flat"

    last3 = pivots.tail(3)

    tipos = []
    valores = []
    for _, row in last3.iterrows():
        if row['pivot_high']:
            tipos.append("H")
            valores.append(row['high'])
        elif row['pivot_low']:
            tipos.append("L")
            valores.append(row['low'])

    if len(tipos) < 3:
        return "flat"

    if (tipos == ["L", "H", "L"] or tipos == ["H", "L", "H"]) and valores[2] > valores[0]:
        return "bullish"
    elif (tipos == ["H", "L", "H"] or tipos == ["L", "H", "L"]) and valores[2] < valores[0]:
        return "bearish"
    else:
        return "flat"

def identificar_soportes_resistencias(df, window=10, tolerance=0.005, top_n=2):
    """
    Identifica niveles de soporte y resistencia y devuelve los top_n más
    cercanos al precio actual (último Close).

    Parámetros:
        df : pd.DataFrame con columnas ['high','low','close']
        window : int para argrelextrema
        tolerance : float para agrupar niveles muy cercanos (proporcional)
        top_n : int número de niveles por tipo a devolver (por defecto 2)
    Retorna:
        soportes_sel, resistencias_sel : listas con hasta top_n niveles (float)
    """
    data = df.copy()

    # Forzar columnas numéricas y normalizar comas decimales
    for col in ("high", "low", "close"):
        if col not in data.columns:
            raise ValueError(f"Falta la columna requerida '{col}'")
        data[col] = pd.to_numeric(data[col].astype(str).str.replace(",", "."), errors="coerce")

    #data = data.dropna(subset=['high','low','close'])
    if data.empty:
        return [], []

    highs_idx = argrelextrema(data['high'].values, np.greater_equal, order=window)[0]
    lows_idx = argrelextrema(data['low'].values, np.less_equal, order=window)[0]

    pivote_highs = data['high'].iloc[highs_idx].values.tolist()
    pivote_lows = data['low'].iloc[lows_idx].values.tolist()

    def agrupar_niveles(niveles):
        niveles = [float(x) for x in niveles if _is_finite_number(x)]
        if not niveles:
            return []
        niveles = sorted(set(niveles))
        grupos = [niveles[0]]
        for nivel in niveles[1:]:
            if grupos[-1] == 0 or abs(nivel - grupos[-1]) / abs(grupos[-1]) > tolerance:
                grupos.append(nivel)
            else:
                # merge simple: promediar
                grupos[-1] = (grupos[-1] + nivel) / 2.0
        return grupos

    resistencias = agrupar_niveles(pivote_highs)
    soportes = agrupar_niveles(pivote_lows)

    # seleccionar los top_n más cercanos al precio actual (último close)
    precio_actual = float(data['close'].iloc[-1])
    def elegir_mas_cercanos(niveles, n):
        if not niveles:
            return []
        niveles = np.array(niveles)
        idx = np.argsort(np.abs(niveles - precio_actual))
        seleccion = niveles[idx][:n].tolist()
        return sorted(seleccion)  # orden ascendente para graficar

    soportes_sel = elegir_mas_cercanos(soportes, top_n)
    resistencias_sel = elegir_mas_cercanos(resistencias, top_n)

    return soportes_sel, resistencias_sel

def _is_finite_number(x):
    try:
        v = float(x)
        return np.isfinite(v)
    except Exception:
        return False


def calcular_rsi(series, period=14):

    # Asegurar que la serie es numérica
    series = pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce")

    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def adicionar_indicadores(df):

    best_fast, best_slow = buscar_smas_optimizados(df['close'])
    print(f"Mejores SMAs encontradas: Fast={best_fast}, Slow={best_slow}")

    #Adds technical indicators to the DataFrame.
    df['SMA_FAST'] = df['close'].rolling(window=best_fast).mean()
    #df['SMA_FAST_DIFF'] = df['SMA_FAST'] - df['SMA_FAST'].shift(1)
    
    df['SMA_SLOW'] = df['close'].rolling(window=best_slow).mean()
    #df['SMA_SLOW_DIFF'] = df['SMA_SLOW'] - df['SMA_SLOW'].shift(1)

    #df['SMA_DIFFERENCE'] = df['SMA_FAST'] - df['SMA_SLOW']
    
    #df['EMA_10'] = df['close'].ewm(span=10, adjust=False).mean()
    
    df['RSI_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    #df['RSI_14_DIFF'] = df['RSI_14'] - df['RSI_14'].shift(1)
    
    #df['Low_prev1'] = df['low'].shift(1)
    #df['Low_prev2'] = df['low'].shift(2)
    #df['High_prev1'] = df['high'].shift(1)
    #df['High_prev2'] = df['high'].shift(2)

    #if not df.index.name or df.index.name != 'Datetime':
    #    df.index = pd.to_datetime(df.index)
    #max_high_per_day = df['high'].groupby(df.index.date).transform('max')
    #min_low_per_day = df['low'].groupby(df.index.date).transform('min')
    #df['IsMaxHighOfDay'] = (df['high'] == max_high_per_day).astype(int)
    #df['IsMinLowOfDay'] = (df['low'] == min_low_per_day).astype(int)
   
    # Delete rows con NaN
    #df = df.dropna()
    return df

def buscar_smas_optimizados(data):
    fast_range = range(3, 21, 2)   # e.g. 3,5,…,19
    slow_range = range(10, 51, 5)  # e.g. 10,15,…,50

    best = {'profit': -np.inf}
    for fw in fast_range:
        for sw in slow_range:
            if fw >= sw:
                continue
            profit, df = moving_average_crossover_profit(data, fw, sw)
            if profit > best['profit']:
                best = {'fast': fw, 'slow': sw, 'profit': profit, 'df': df.copy()}
    return best['fast'], best['slow']

def moving_average_crossover_profit(prices, fast_window, slow_window):
    """
    Compute profit for simple moving average crossover strategy:
    - Buy when fast SMA crosses above slow SMA
    - Sell when fast SMA crosses below slow SMA
    """
    if fast_window >= slow_window:
        return -np.inf  # invalid parameter set
    
    df = pd.DataFrame({'price': prices})
    df['fast_sma'] = prices.rolling(window=fast_window).mean()
    df['slow_sma'] = prices.rolling(window=slow_window).mean()
    df.dropna(inplace=True)
    
    df['signal'] = 0
    df.loc[df.fast_sma > df.slow_sma, 'signal'] = 1
    df['position'] = df['signal'].diff()
    
    # Buy at position == +1, sell at -1
    buys = df[df['position'] == 1]['price']
    sells = df[df['position'] == -1]['price']
    
    # If ends in position = 1, sell at last price
    if df['signal'].iloc[-1] == 1:
        sells = sells._append(pd.Series(df['price'].iloc[-1], index=[df.index[-1]]))
    
    profit = sells.values.sum() - buys.values.sum()
    return profit, df

def grid_search_params(prices, fast_range, slow_range):
    """
    Grid search over ranges of fast-moving and slow-moving windows.
    Returns best (fast, slow, profit, df_of_best).
    """
    best = {'profit': -np.inf}
    for fw in fast_range:
        for sw in slow_range:
            if fw >= sw:
                continue
            profit, df = moving_average_crossover_profit(prices, fw, sw)
            if profit > best['profit']:
                best = {'fast': fw, 'slow': sw, 'profit': profit, 'df': df.copy()}
    return best


## --------------------------Graficar -------------------

def graficar_pivots(df, symbol="Activo"):

    # Forzar renderer a browser para mayor fiabilidad
    pio.renderers.default = "browser"

    # Copia y limpieza de datos OHLC
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    for c in ['open', 'high', 'low', 'close']:
        data[c] = pd.to_numeric(data[c], errors='coerce')
    #data = data.dropna(subset=['open', 'high', 'low', 'close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    tendencia = determinar_tendencia(df)

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Precio'
    )])

    # Pivots High
    df_highs = data.loc[df.index[df['pivot_high']]] if 'pivot_high' in df.columns else data.iloc[0:0]
    if not df_highs.empty:
        fig.add_trace(go.Scatter(
            x=df_highs.index,
            y=df_highs['high'],
            mode='markers+text',
            marker=dict(color='red', size=10),
            text=df_highs.get('pivot_label', None),
            textposition='top center',
            name='Pivots High'
        ))

    # Pivots Low
    df_lows = data.loc[df.index[df['pivot_low']]] if 'pivot_low' in df.columns else data.iloc[0:0]
    if not df_lows.empty:
        fig.add_trace(go.Scatter(
            x=df_lows.index,
            y=df_lows['low'],
            mode='markers+text',
            marker=dict(color='green', size=10),
            text=df_lows.get('pivot_label', None),
            textposition='bottom center',
            name='Pivots Low'
        ))

    fig.update_layout(
        title=f"Pivots - {symbol} | {tendencia}",
        yaxis_title='Precio',
        xaxis_title='Fecha',
        template='plotly_white',
        width=1200,
        height=700,
        xaxis_rangeslider_visible=False,
        xaxis_type='category',
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    # Mostrar; si falla, guardar HTML y abrir en navegador
    try:
        fig.show()
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), f"pivots_{symbol}.html")
        fig.write_html(tmp, auto_open=True)
        try:
            webbrowser.open(f"file://{tmp}")
        except Exception:
            print(f"Gráfica guardada en: {tmp}")

def graficar_soportes_resistencias_plotly(df, soportes, resistencias, titulo="Soportes y Resistencias", symbol="Activo"):
    """
    Grafica velas con Plotly y dibuja líneas horizontales para soportes/resistencias.
    """
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    data = data.dropna(subset=['open','high','low','close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Precio'
    )])

    shapes = []
    annotations = []
    last_x = data.index[-1]

    # Añadir resistencias (líneas rojas)
    for i, nivel in enumerate(resistencias):
        shapes.append(dict(type='line', x0=data.index[0], x1=last_x, xref='x', y0=nivel, y1=nivel,
                           yref='y', line=dict(color='red', width=1.5, dash='dash')))
        annotations.append(dict(x=last_x, y=nivel, xref='x', yref='y',
                                text=f"R{i+1}: {nivel:.4f}", showarrow=False,
                                xanchor='left', font=dict(color='red')))

    # Añadir soportes (líneas verdes)
    for i, nivel in enumerate(soportes):
        shapes.append(dict(type='line', x0=data.index[0], x1=last_x, xref='x', y0=nivel, y1=nivel,
                           yref='y', line=dict(color='green', width=1.5, dash='dash')))
        annotations.append(dict(x=last_x, y=nivel, xref='x', yref='y',
                                text=f"S{i+1}: {nivel:.4f}", showarrow=False,
                                xanchor='left', font=dict(color='green')))

    fig.update_layout(title=f"{symbol} - {titulo}", shapes=shapes, annotations=annotations,
                      yaxis_title='Precio', xaxis_title='Fecha',
                      template='plotly_white', xaxis_rangeslider_visible=False,
                      width=1200, height=700)

    try:
        fig.show()
    except Exception:
        # fallback: guardar html y abrir navegador
        import tempfile, webbrowser, os
        tmp = os.path.join(tempfile.gettempdir(), f"soportes_resistencias_{symbol}.html")
        fig.write_html(tmp, auto_open=True)

def graficar_pivots_soportes_resistencias_2(df, soportes, resistencias, symbol="Activo", tendencia="", rsi=0,
                                          sma_fast_col='SMA_FAST', sma_slow_col='SMA_SLOW', name="defaul", timeframe="1D"):
    """
    Grafica los pivotes, soportes y resistencias en un solo gráfico.
    """
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    #data = data.dropna(subset=['open','high','low','close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Precio'
    )])

    data_pivots = df.copy()
    data_pivots.index = pd.to_datetime(data_pivots.index)
    for c in ['open', 'high', 'low', 'close']:
        data_pivots[c] = pd.to_numeric(data_pivots[c], errors='coerce')
    data_pivots = data_pivots.dropna(subset=['open', 'high', 'low', 'close'])

    #pivots high
    df_highs = data_pivots.loc[data_pivots.index[data_pivots['pivot_high']]] if 'pivot_high' in data_pivots.columns else data_pivots.iloc[0:0]
    if not df_highs.empty:
        fig.add_trace(go.Scatter(
            x=df_highs.index,
            y=df_highs['high'],
            mode='markers+text',
            marker=dict(color='red', size=10),
            text=df_highs.get('pivot_label', None),
            textposition='top center',
            name='Pivots High'
        ))

    # Pivots Low
    df_lows = data_pivots.loc[data_pivots.index[data_pivots['pivot_low']]] if 'pivot_low' in data_pivots.columns else data_pivots.iloc[0:0]
    if not df_lows.empty:
        fig.add_trace(go.Scatter(
            x=df_lows.index,
            y=df_lows['low'],
            mode='markers+text',
            marker=dict(color='green', size=10),
            text=df_lows.get('pivot_label', None),
            textposition='bottom center',
            name='Pivots Low'
        ))

    # Graficar soportes
    for i, nivel in enumerate(soportes):
        fig.add_trace(go.Scatter(
            x=[data.index[0], data.index[-1]],
            y=[nivel, nivel],
            mode='lines',
            line=dict(color='green', width=1.5, dash='dash'),
            name=f"Soporte {i+1}"
        ))

    # Graficar resistencias
    for i, nivel in enumerate(resistencias):
        fig.add_trace(go.Scatter(
            x=[data.index[0], data.index[-1]],
            y=[nivel, nivel],
            mode='lines',
            line=dict(color='red', width=1.5, dash='dash'),
            name=f"Resistencia {i+1}"
        )) 

    # Añadir SMAs si existen
    if sma_fast_col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[sma_fast_col],
                                 mode='lines', name=sma_fast_col,
                                 line=dict(color='orange', width=1.5)))
    if sma_slow_col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[sma_slow_col],
                                 mode='lines', name=sma_slow_col,
                                 line=dict(color='blue', width=1.5)))


    fig.update_layout(
        title = f"{name} ({symbol}) {timeframe} - Tendencia: {tendencia} - RSI: {str(data['RSI_14'].iloc[-1].round(2))}",
        yaxis_title='Precio',
        yaxis=dict(automargin=True),
        xaxis=dict(
            #type='category',
            #tickformat='dd-mm-yy HH:MM',
            tickangle=-45,
            tickmode='auto',
            tickfont=dict(size=10),
            rangeslider=dict(visible=False )       ),
        template='plotly_white',
        width=1200,
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    try:
        fig.show()
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), f"pivots_soportes_resistencias_{symbol}.html")
        fig.write_html(tmp, auto_open=True)


def graficar_pivots_soportes_resistencias(df, pivots, soportes, resistencias, symbol="Activo", tendencia="", rsi=0,
                                          sma_fast_col='SMA_FAST', sma_slow_col='SMA_SLOW', name="defaul", timeframe="1D"):
    """
    Grafica los pivotes, soportes y resistencias en un solo gráfico.
    """
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    data = data.dropna(subset=['open','high','low','close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Precio'
    )])

    data_pivots = pivots.copy()
    data_pivots.index = pd.to_datetime(data_pivots.index)
    for c in ['open', 'high', 'low', 'close']:
        data_pivots[c] = pd.to_numeric(data_pivots[c], errors='coerce')
    data_pivots = data_pivots.dropna(subset=['open', 'high', 'low', 'close'])

    #pivots high
    df_highs = data_pivots.loc[pivots.index[pivots['pivot_high']]] if 'pivot_high' in pivots.columns else data_pivots.iloc[0:0]
    if not df_highs.empty:
        fig.add_trace(go.Scatter(
            x=df_highs.index,
            y=df_highs['high'],
            mode='markers+text',
            marker=dict(color='red', size=10),
            text=df_highs.get('pivot_label', None),
            textposition='top center',
            name='Pivots High'
        ))

    # Pivots Low
    df_lows = data_pivots.loc[pivots.index[pivots['pivot_low']]] if 'pivot_low' in pivots.columns else data_pivots.iloc[0:0]
    if not df_lows.empty:
        fig.add_trace(go.Scatter(
            x=df_lows.index,
            y=df_lows['low'],
            mode='markers+text',
            marker=dict(color='green', size=10),
            text=df_lows.get('pivot_label', None),
            textposition='bottom center',
            name='Pivots Low'
        ))

    # Graficar soportes
    for i, nivel in enumerate(soportes):
        fig.add_trace(go.Scatter(
            x=[data.index[0], data.index[-1]],
            y=[nivel, nivel],
            mode='lines',
            line=dict(color='green', width=1.5, dash='dash'),
            name=f"Soporte {i+1}"
        ))

    # Graficar resistencias
    for i, nivel in enumerate(resistencias):
        fig.add_trace(go.Scatter(
            x=[data.index[0], data.index[-1]],
            y=[nivel, nivel],
            mode='lines',
            line=dict(color='red', width=1.5, dash='dash'),
            name=f"Resistencia {i+1}"
        )) 

    # Añadir SMAs si existen
    if sma_fast_col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[sma_fast_col],
                                 mode='lines', name=sma_fast_col,
                                 line=dict(color='orange', width=1.5)))
    if sma_slow_col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[sma_slow_col],
                                 mode='lines', name=sma_slow_col,
                                 line=dict(color='blue', width=1.5)))


    fig.update_layout(
        title = f"{name} ({symbol}) {timeframe} - Tendencia: {tendencia} - RSI: {str(data['RSI_14'].iloc[-1].round(2))}",
        yaxis_title='Precio',
        yaxis=dict(automargin=True),
        xaxis=dict(
            #type='category',
            #tickformat='dd-mm-yy HH:MM',
            tickangle=-45,
            tickmode='auto',
            tickfont=dict(size=10),
            rangeslider=dict(visible=False )       ),
        template='plotly_white',
        width=1200,
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    try:
        fig.show()
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), f"pivots_soportes_resistencias_{symbol}.html")
        fig.write_html(tmp, auto_open=True)


def format_datetime_index(df, fmt='%d-%m-%y %H:%M', tz=None, localize=None,
                          drop_timezone=True, add_str_column=False, col_name='DatetimeStr', inplace=False):
    """
    Asegura que el índice sea DatetimeIndex, opcionalmente localiza/convierte timezone,
    opcionalmente elimina la zona horaria y crea una columna con la fecha formateada.

    Parámetros:
      - df: DataFrame
      - fmt: formato de salida para la columna string (strftime), por defecto 'dd-mm-yy HH:MM'
      - tz: convierte el índice a este timezone (ej. 'UTC', 'Europe/Madrid') si no es None
      - localize: si el índice es naive y localize no es None, hace tz_localize(localize)
      - drop_timezone: si True, al final quita la info de timezone (index tz naive)
      - add_str_column: si True, añade columna `col_name` con index.strftime(fmt)
      - col_name: nombre de la columna a crear si add_str_column=True
      - inplace: si True modifica df en sitio y devuelve el mismo DataFrame

    Retorna:
      DataFrame con índice datetime normalizado (y columna formateada si se pidió).
    """
    if not inplace:
        df = df.copy()
    # asegurar DatetimeIndex
    df.index = pd.to_datetime(df.index, errors='coerce')
    if df.index.isnull().any():
        # eliminar filas con índices no parseables
        df = df[~df.index.isnull()]

    # localizar timezone si se solicita y el índice es naive
    try:
        if localize is not None and df.index.tz is None:
            df.index = df.index.tz_localize(localize)
    except Exception:
        pass

    # convertir timezone si se solicita
    try:
        if tz is not None:
            # si aún no tiene tz y no se pidió localize, localize a UTC antes de convertir
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            df.index = df.index.tz_convert(tz)
    except Exception:
        pass

    # opcional: quitar tz info para dejar índices naive
    try:
        if drop_timezone and df.index.tz is not None:
            df.index = df.index.tz_localize(None)
    except Exception:
        pass

    # añadir columna string con formato deseado
    if add_str_column:
        df[col_name] = df.index.strftime(fmt)

    return df




def csv_to_pd(symbol_timeframe):
    """Utility function to extract a pandas dataframe from a CSV file.
        param symbol_timeframe: str "SYMBOL_TIMEFRAME"
        return: pandas dataframe        
    """
    
    #DATA_DIR = Path(parameters.OUT_DIR)  
    #filepath = DATA_DIR / f"{symbol_timeframe}.csv"
    filepath = Path(r"C:\repo_luis\Rafa\received_data") / f"{symbol_timeframe}.csv"

    dataframe = {}
    
    try:
        data = pd.read_csv(filepath, parse_dates=['datetime'], index_col='datetime')
        dataframe[symbol_timeframe] = data
        print(f"Datos convertidos para {symbol_timeframe}:")
        return dataframe[symbol_timeframe]
    except Exception as e:
        print(f"Error al convertir {symbol_timeframe}: {e}")
        return None

def normalize_data_types(df):
    """
    Asegura que las columnas OHLC sean numéricas y maneja comas decimales.
    Elimina filas con datos no convertibles.
    """
    df = df.copy()
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors='coerce')
    #df = df.dropna(subset=['open', 'high', 'low', 'close'])
    return df

def graficar(symbol_timeframe):
    df = csv_to_pd(symbol_timeframe)
    df = normalize_data_types(df)

    symbol, timeframe = symbol_timeframe.split("_")

    #df_pivots = utility.identificar_pivots(df, 2)
    #print(df_pivots.tail(10))

    df = identificar_pivots(df, 2)

    soportes, resistencias = identificar_soportes_resistencias(df, window=10, tolerance=0.005, top_n=5)

    #tendencia = utility.determinar_tendencia(df_pivots, 2)
    tendencia = determinar_tendencia(df, 3)

    rsi = calcular_rsi(df['close'], period=14)

    adicionar_indicadores(df)

    df = df.sort_index().tail(80)
    #df_pivots = df_pivots.sort_index().tail(80)

    print("df:")
    print(df.tail(10))
    #print("df_pivots:") 
    #print(df_pivots.tail(10))

    #utility.graficar_pivots_soportes_resistencias(df, df_pivots, soportes, resistencias, "6A", tendencia, rsi, name="6A", timeframe="15m")
    #graficar_pivots_soportes_resistencias_2(df, soportes, resistencias, symbol, tendencia, rsi, name="6A", timeframe=timeframe)

    save_bars_csv(symbol, timeframe, df)

    #--- actualizar archivo
_FILE_SAVE_LOCK = threading.Lock()

def save_bars_csv(symbol, timeframe, df, out_dir=None):

    #df = bars_to_df(df)       
    if out_dir is None:
        out_dir = os.path.join(parameters.OUT_DIR)
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{symbol}_{timeframe}.csv"
    out_path = os.path.join(out_dir, filename)

    with _FILE_SAVE_LOCK:
        df.to_csv(out_path, index=True)
        
def bars_to_df(bars):
    """Normaliza 'bars' (lista de dicts o dict de listas) a DataFrame con columna 'datetime'."""
    if isinstance(bars, dict):
        df = pd.DataFrame(bars)
    else:
        df = pd.DataFrame(bars)

    datetime_cols = [c for c in df.columns if c.lower() in ("datetime", "time", "timestamp", "date")]
    if datetime_cols:
        dt_col = datetime_cols[0]
        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
        if dt_col != "datetime":
            df = df.rename(columns={dt_col: "datetime"})
    else:
        df["datetime"] = pd.NaT

    return df
##---- db functions

def write_db(symbol, timeframe, trend, rsi, soportes, resistencias):
    engine = create_engine(
    "postgresql+psycopg2://admin:admin123@localhost:5432/trading_db"
    )

    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO info (simbolo, timeframe, tendencia, rsi, soportes, resistencias)
            VALUES (:s, :t, :td, :r, :sp, :rs )
            ON CONFLICT (simbolo, timeframe)
            DO UPDATE SET
                tendencia = EXCLUDED.tendencia,
                rsi = EXCLUDED.rsi,
                ts = CURRENT_TIMESTAMP,
                soportes = EXCLUDED.soportes,
                resistencias = EXCLUDED.resistencias;
        """), 
        {"s": symbol, "t": timeframe, "td": trend, "r":rsi, "sp": soportes, "rs": resistencias})




