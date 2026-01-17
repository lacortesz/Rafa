import os
import json
from pathlib import Path
import pandas as pd
from scipy.signal import argrelextrema
import numpy as np
import utility.parameters as parameters
import plotly.graph_objects as go
import tempfile
import ta
import threading
from sqlalchemy import create_engine, text


try:
    from confluent_kafka import Producer    
except Exception:
    Producer = None

producer = None

##----- kafka functions
def init_kafka_producer(bootstrap_servers=None):
    """Initialize and store a confluent_kafka Producer in this module.

    bootstrap_servers: str, e.g. 'localhost:9092'. If None, read from env KAFKA_BOOTSTRAP.
    Returns the producer instance or None on failure.
    """
    global producer
    if Producer is None:
        print("confluent_kafka.Producer not available in environment")
        producer = None
        return None

    bs = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP", "localhost:8003")
    try:
        conf = {"bootstrap.servers": bs,
                "client.id": "process-data-producer",
                "acks": "all",                # asegura confirmación del broker
                "retries": 3,                 # reintentos automáticos
                "linger.ms": 5,               # agrupa mensajes para eficiencia
                "delivery.timeout.ms": 30000  # timeout total
                }
        producer = Producer(conf)
        print(f"Kafka producer initialized (bootstrap={bs})")
        return producer
    except Exception as e:
        producer = None
        print("Failed to initialize Kafka producer:", e)
        return None
    
def publish_to_kafka(message, topic, timeout=5):
    """Blocking publish of `message` (dict) to `topic` using the module-level producer.

    Raises any exceptions from confluent_kafka to the caller.
    """
    if producer is None:
        raise RuntimeError("Kafka producer not initialized")

    def delivery_report(err, msg):
        if err is not None:
            print("Kafka delivery failed:", err)
        else:
            try:
                print(f"Kafka message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
            except Exception:
                print("Kafka message delivered (meta unavailable)")

    producer.produce(topic, json.dumps(message).encode("utf-8"), callback=delivery_report)
    producer.flush(timeout=timeout)


def send_result(result, topic=None):
    """Convenience wrapper to publish result to Kafka topic (sync/blocking).

    Designed to be called from `run_in_executor` or directly in blocking contexts.
    """
    t = topic or os.getenv("KAFKA_TOPIC_DATA_GATEWAY", "data_gateway")
    publish_to_kafka(result, t)

def message_json(payload):
    symbol, timeframe = get_symbol_timeframe(payload)
    
    data = {
    "accion": "archivo procesado",
    "symbol_timeframe": f"{symbol}_{timeframe}"
    }

    return json.dumps(data)


##----- data processing functions
def process_file(payload):
    """
    Main data processing function.
    param:
    payload: dict with keys 'symbol' and 'timeframe'
    """
    #0. inicialize variables
    df = {}
    
    #1. Process the incoming data payload to get symbol and timeframe
    symbol, timeframe = get_symbol_timeframe(payload)
    if symbol == None or timeframe == None:
        print("Invalid payload, missing symbol or timeframe:", payload)
        return
    
    symbol_timeframe = f"{symbol}_{timeframe}"
    
    #2. read csv file and convert to pd dataframe
    df = csv_to_pd(symbol_timeframe)
    
    if df is None:
        print("Failed to open file:", symbol_timeframe)
        return
    
    df = normalize_data_types(df)

    #3. Get trend
    df = identificar_pivots(df, parameters.pivotStrength )
    tendencia = determinar_tendencia(df,3)
    print(f"tendencia para  {symbol} - {timeframe} : {tendencia}")

    #4. Add indicators
    soportes, resistencias = identificar_soportes_resistencias(df, window = 10, tolerance=0.005, top_n=5)
    df = adicionar_indicadores(df)
    rsi = float(df['RSI_14'].iloc[-1].round(2))

    df = df.sort_index().tail(80)

    #graficar_pivots_soportes_resistencias(df, soportes, resistencias, symbol, tendencia, rsi, name="", timeframe=timeframe)

    #4. storege data (csv file or BD) for each symbol and timeframe 

    save_bars_csv(symbol, timeframe, df)

    write_db(symbol, timeframe, tendencia, rsi, soportes, resistencias)


##----- process data function

def get_symbol_timeframe(payload):
    """Get symbol and timeframe from payload dict.
        param payload: dict with keys 'symbol' and 'timeframe'
        return: str "SYMBOL_TIMEFRAME"
    """
    
    symbol= payload.get("symbol")
    timeframe = payload.get("timeframe")
    return symbol, timeframe
 
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
    #df.dropna(inplace=True)
    
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

##---- Graficar

def graficar_pivots_soportes_resistencias(df, soportes, resistencias, symbol="Activo", tendencia="", rsi=0,
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
    #data_pivots = data_pivots.dropna(subset=['open', 'high', 'low', 'close'])

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

##--- Database

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


##--- write file

_FILE_SAVE_LOCK = threading.Lock()

def save_bars_csv(symbol, timeframe, df, out_dir=None):

    #df = bars_to_df(df)       
    if out_dir is None:
        #out_dir = os.path.join(parameters.OUT_DIR_2)
        out_dir = os.path.join(parameters.OUT_DIR)

    os.makedirs(out_dir, exist_ok=True)

    filename = f"{symbol}_{timeframe}.csv"
    out_path = os.path.join(out_dir, filename)

    with _FILE_SAVE_LOCK:
        df.to_csv(out_path, index=True)