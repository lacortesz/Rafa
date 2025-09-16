import yfinance as yf
import ta 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

symbols = {
    '6EZ25.CME': "Euro Dólar"
}


def download_data(ticker, start, end, interval):
    
    # Downloads historical market data for a given ticker symbol.
    df = yf.download(ticker, start=start, end=end, interval=interval, multi_level_index=False)
    if df.empty:
        raise ValueError(f"No data fetched for {ticker}. Check ticker or date range.")
    return df

def add_indicators(df, best_fast, best_slow):
    #Adds technical indicators to the DataFrame.
    df['SMA_FAST'] = df['Close'].rolling(window=best_fast).mean()
    df['SMA_FAST_DIFF'] = df['SMA_FAST'] - df['SMA_FAST'].shift(1)
    
    df['SMA_SLOW'] = df['Close'].rolling(window=best_slow).mean()
    df['SMA_SLOW_DIFF'] = df['SMA_SLOW'] - df['SMA_SLOW'].shift(1)

    df['SMA_DIFFERENCE'] = df['SMA_FAST'] - df['SMA_SLOW']
    
    #df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
    
    df['RSI_14'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['RSI_14_DIFF'] = df['RSI_14'] - df['RSI_14'].shift(1)
    
    df['Low_prev1'] = df['Low'].shift(1)
    df['Low_prev2'] = df['Low'].shift(2)
    df['High_prev1'] = df['High'].shift(1)
    df['High_prev2'] = df['High'].shift(2)

    if not df.index.name or df.index.name != 'Datetime':
        df.index = pd.to_datetime(df.index)
    max_high_per_day = df['High'].groupby(df.index.date).transform('max')
    min_low_per_day = df['Low'].groupby(df.index.date).transform('min')
    df['IsMaxHighOfDay'] = (df['High'] == max_high_per_day).astype(int)
    df['IsMinLowOfDay'] = (df['Low'] == min_low_per_day).astype(int)
   
    # Delete rows con NaN
    df = df.dropna()
    return df

def find_optimize_smas(data):
    fast_range = range(3, 21, 2)   # e.g. 3,5,…,19
    slow_range = range(10, 51, 5)  # e.g. 10,15,…,50

    return grid_search_params(data, fast_range, slow_range)

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

def plot(df, ticker, best):
    plt.figure(figsize=(14,7))
    plt.plot(df.index, df['price'], label='Close Price', color='black')
    plt.plot(df.index, df['fast_sma'], label=f'Fast SMA ({best["fast"]})', color='blue')
    plt.plot(df.index, df['slow_sma'], label=f'Slow SMA ({best["slow"]})', color='red')

    # Mark buy/sell signals
    buys = df[df['position'] == 1]
    sells = df[df['position'] == -1]
    plt.scatter(buys.index, buys['price'], marker='^', color='green', label='Buy', s=100)
    plt.scatter(sells.index, sells['price'], marker='v', color='magenta', label='Sell', s=100)

    plt.title(f"{ticker} Price and MA Crossover (Profit: {best['profit']:.2f})")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.show()

def train_predict_minmax(df):
    features = [
        'SMA_FAST', 'SMA_FAST_DIFF', 'SMA_SLOW', 'SMA_SLOW_DIFF', 'SMA_DIFFERENCE',
        'RSI_14', 'RSI_14_DIFF', 'Low_prev1', 'Low_prev2', 'High_prev1', 'High_prev2'
    ]
    # Eliminar filas con NaN en features o etiquetas
    df_ml = df.dropna(subset=features + ['IsMinLowOfDay', 'IsMaxHighOfDay'])
    X = df_ml[features]
    y_min = df_ml['IsMinLowOfDay']
    y_max = df_ml['IsMaxHighOfDay']

    # Split para min low
    X_train, X_test, y_train, y_test = train_test_split(X, y_min, test_size=0.2, random_state=42)
    clf_min = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_min.fit(X_train, y_train)
    y_pred = clf_min.predict(X_test)
    print('Reporte clasificación para MinLow:')
    print(classification_report(y_test, y_pred))

    # Split para max high
    X_train, X_test, y_train, y_test = train_test_split(X, y_max, test_size=0.2, random_state=42)
    clf_max = RandomForestClassifier(n_estimators=100, random_state=42)
    clf_max.fit(X_train, y_train)
    y_pred = clf_max.predict(X_test)
    print('Reporte clasificación para MaxHigh:')
    print(classification_report(y_test, y_pred))

    return clf_min, clf_max

if __name__ == "__main__":
    
    # Descargar datos
    ticker = '6EZ25.CME'
    data = download_data(ticker, '2025-01-01', '2025-08-01', '1h')
    #print(data)
    
    # Optimizar SMAs
    best = find_optimize_smas(data['Close'])
    print(f"Best parameters: fast={best['fast']}, slow={best['slow']}, profit={best['profit']:.2f}")
    
    # Añadir indicadores técnicos
    data_with_indicators = add_indicators(data, best['fast'], best['slow'])
    print(data_with_indicators)
    
    # Entrenar modelos ML para predecir min low y max high
    clf_min, clf_max = train_predict_minmax(data_with_indicators)

    '''
    # Filtrar y mostrar solo los registros donde IsMinLowOfDay es 1
    min_low_df = data_with_indicators[data_with_indicators['IsMMinLowOfDay'] == 1]
    print('Registros con máximo High del día:')
    print(max_high_df)
    '''

    # pruebas de predict
    new_data = download_data(ticker, '2025-08-01', '2025-09-12', '1h')
    new_data_with_indicators = add_indicators(new_data, best['fast'], best['slow'])
    features = [
        'SMA_FAST', 'SMA_FAST_DIFF', 'SMA_SLOW', 'SMA_SLOW_DIFF', 'SMA_DIFFERENCE',
        'RSI_14', 'RSI_14_DIFF', 'Low_prev1', 'Low_prev2', 'High_prev1', 'High_prev2'
    ]       
    X_new = new_data_with_indicators[features].dropna()
    min_low_pred = clf_min.predict(X_new)   
    max_high_pred = clf_max.predict(X_new)
    new_data_with_indicators = new_data_with_indicators.loc[X_new.index]
    new_data_with_indicators['MaxHighPred'] = max_high_pred
    new_data_with_indicators['MinLowPred'] = min_low_pred
    print(new_data_with_indicators[['Close', 'High', 'MinLowPred', 'MaxHighPred']])

    min_low_df = new_data_with_indicators[new_data_with_indicators['IsMinLowOfDay'] > 0]
    max_high_df = new_data_with_indicators[new_data_with_indicators['IsMaxHighOfDay'] > 0]

    print('Registros con mínimo Low del día:')
    print(min_low_df)
    print('Registros con máximo High del día:')
    print(max_high_df)

    #descarga a csv
    new_data_with_indicators.to_csv('predictions.csv')
    # Plot setup
    df = best['df']

    plot(df, ticker, best)

