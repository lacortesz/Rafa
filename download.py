import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import ta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

symbol = '6EZ25.CME'
intervalos = {'1h': 'euro_dolar_1h.csv'}

def add_indicators(df):
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_10_DIFF'] = df['SMA_10'] - df['SMA_10'].shift(1)
    df['SMA_25'] = df['Close'].rolling(window=25).mean()
    df['SMA_25_DIFF'] = df['SMA_25'] - df['SMA_25'].shift(1)
    df['SMA_DIFFERENCE'] = df['SMA_10'] - df['SMA_25']
    df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['RSI_14'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['RSI_14_DIFF'] = df['RSI_14'] - df['RSI_14'].shift(1)
    df['Low_prev1'] = df['Low'].shift(1)
    df['Low_prev2'] = df['Low'].shift(2)
    df['High_prev1'] = df['High'].shift(1)
    df['High_prev2'] = df['High'].shift(2)
    if not df.index.name or df.index.name != 'Datetime':
        df.index = pd.to_datetime(df.index)
    min_per_day = df['Low'].groupby(df.index.date).transform('min')
    max_per_day = df['High'].groupby(df.index.date).transform('max')
    df['Min_per_day'] = min_per_day
    df['Max_per_day'] = max_per_day
    df['MinMaxFlag'] = 0
    df.loc[df['Low'] == min_per_day, 'MinMaxFlag'] = -1
    df.loc[df['High'] == max_per_day, 'MinMaxFlag'] = 1
    df['MinCloseFlag'] = 0
    df['MaxHighFlag'] = 0
    min_close_per_day = df['Close'].groupby(df.index.date).transform('min')
    max_high_per_day = df['High'].groupby(df.index.date).transform('max')
    df.loc[df['Close'] == min_close_per_day, 'MinCloseFlag'] = 1
    df.loc[df['High'] == max_high_per_day, 'MaxHighFlag'] = 1
    return df

def plot_candlestick_interactive(df, title='Candlestick Chart'):
    df_candle = df[['Open', 'High', 'Low', 'Close']].copy()
    df_candle.index = pd.to_datetime(df.index)
    fig = go.Figure(data=[go.Candlestick(
        x=df_candle.index,
        open=df_candle['Open'],
        high=df_candle['High'],
        low=df_candle['Low'],
        close=df_candle['Close'])])
    fig.update_layout(title=title, xaxis_title='Fecha', yaxis_title='Precio', xaxis_rangeslider_visible=True)
    fig.show()

def train_and_predict(symbol, intervalo, train_start, train_end, test_start, test_end, archivo):
    print(f"Descargando datos de entrenamiento para {intervalo}")
    df_train = yf.download(symbol, start=train_start, end=train_end, interval=intervalo, multi_level_index=False)
    df_train = df_train.dropna()
    df_train = add_indicators(df_train)
    df_train.to_csv(archivo)
    plot_candlestick_interactive(df_train, title=f'Candlestick train {intervalo}')

    features = [
        'SMA_10', 'SMA_10_DIFF', 'SMA_25', 'SMA_25_DIFF', 'SMA_DIFFERENCE',
        'EMA_10', 'RSI_14', 'RSI_14_DIFF', 'Low_prev1', 'Low_prev2', 'High_prev1', 'High_prev2'
    ]
    df_ml = df_train.dropna(subset=features)
    X = df_ml[features]
    y_minclose = df_ml['MinCloseFlag']
    y_maxhigh = df_ml['MaxHighFlag']

    X_train, X_test, y_minclose_train, y_minclose_test = train_test_split(X, y_minclose, test_size=0.2, random_state=42)
    _, _, y_maxhigh_train, y_maxhigh_test = train_test_split(X, y_maxhigh, test_size=0.2, random_state=42)

    minclose_model = RandomForestRegressor(n_estimators=100, random_state=42)
    maxhigh_model = RandomForestRegressor(n_estimators=100, random_state=42)
    minclose_model.fit(X_train, y_minclose_train)
    maxhigh_model.fit(X_train, y_maxhigh_train)

    y_minclose_pred = minclose_model.predict(X_test)
    y_maxhigh_pred = maxhigh_model.predict(X_test)

    print(f"MSE MinCloseFlag: {mean_squared_error(y_minclose_test, y_minclose_pred):.4f}")
    print(f"MSE MaxHighFlag: {mean_squared_error(y_maxhigh_test, y_maxhigh_pred):.4f}")

    print("Descargando datos de prueba para {}...".format(intervalo))
    df_test = yf.download(symbol, start=test_start, end=test_end, interval=intervalo, multi_level_index=False)
    df_test = df_test.dropna()
    df_test = add_indicators(df_test)
    plot_candlestick_interactive(df_test, title=f'Candlestick test {intervalo}')

    X_new = df_test[features]
    minclose_pred_test = minclose_model.predict(X_new)
    maxhigh_pred_test = maxhigh_model.predict(X_new)
    df_test['MinCloseProb'] = minclose_pred_test
    df_test['MaxHighProb'] = maxhigh_pred_test
    print(df_test[['Close', 'High', 'MinCloseProb', 'MaxHighProb']])
    return df_train, df_test

for intervalo, archivo in intervalos.items():
    train_and_predict(symbol, intervalo, '2025-01-01', '2025-07-01', '2025-08-01', '2025-10-09', archivo)


# Descarga nueva data
new_df = yf.download(symbol, start='2025-08-01', end='2025-09-01', interval='1h', multi_level_index=False)
new_df = new_df.dropna()
new_df = add_indicators(new_df)

# Selecciona los features
features = [
    'SMA_10', 'SMA_10_DIFF', 'SMA_25', 'SMA_25_DIFF', 'SMA_DIFFERENCE',
    'EMA_10', 'RSI_14', 'RSI_14_DIFF', 'Low_prev1', 'Low_prev2', 'High_prev1', 'High_prev2'
]
X_new = new_df[features]

# Predice
#minclose_pred = minclose_model.predict(X_new)
#maxhigh_pred = maxhigh_model.predict(X_new)

# Agrega las predicciones al DataFrame
#new_df['MinCloseProb'] = minclose_pred
#new_df['MaxHighProb'] = maxhigh_pred

print(new_df[['Close', 'High', 'MinCloseProb', 'MaxHighProb']])	