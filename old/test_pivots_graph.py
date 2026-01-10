import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf

def identificar_pivots(df, n=2):
    """
    Identifica pivots en un DataFrame de precios OHLC.
    Parámetros:
        df (pd.DataFrame): debe contener columnas ['High', 'Low']
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
        if df['High'].iloc[i] == max(df['High'].iloc[i - n:i + n + 1]):
            df.loc[df.index[i], 'pivot_high'] = True

        # Pivot Low
        if df['Low'].iloc[i] == min(df['Low'].iloc[i - n:i + n + 1]):
            df.loc[df.index[i], 'pivot_low'] = True

    # Clasificar pivots como HH, LH, HL, LL
    last_high = None
    last_low = None

    for i in range(len(df)):
        if df['pivot_high'].iloc[i]:
            if last_high is not None:
                label = "HH" if df['High'].iloc[i] > last_high else "LH"
            else:
                label = "H"
            df.loc[df.index[i], 'pivot_label'] = label
            last_high = df['High'].iloc[i]

        elif df['pivot_low'].iloc[i]:
            if last_low is not None:
                label = "HL" if df['Low'].iloc[i] > last_low else "LL"
            else:
                label = "L"
            df.loc[df.index[i], 'pivot_label'] = label
            last_low = df['Low'].iloc[i]

    return df


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
                if pivots['High'].iloc[i] > pivots['High'].iloc[i - 1]:
                    indices_a_eliminar.append(prev_idx)
                else:
                    indices_a_eliminar.append(curr_idx)
            else:
                # Dejar solo el más bajo
                if pivots['Low'].iloc[i] < pivots['Low'].iloc[i - 1]:
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


def determinar_tendencia(df):
    """
    Determina la tendencia basada en los últimos 3 pivots (H/L).
    Reglas:
      - Si últimos 3 pivots son: Low -> High -> Low mayor → Bullish
      - Si últimos 3 pivots son: High -> Low -> High menor → Bearish
      - En cualquier otro caso → Sin tendencia
    """
    pivots = df[df['pivot_label'].notnull()][['pivot_high', 'pivot_low', 'pivot_label', 'High', 'Low']]

    if len(pivots) < 3:
        return "Sin tendencia (pocos pivots)"

    last3 = pivots.tail(3)

    tipos = []
    valores = []
    for _, row in last3.iterrows():
        if row['pivot_high']:
            tipos.append("H")
            valores.append(row['High'])
        elif row['pivot_low']:
            tipos.append("L")
            valores.append(row['Low'])

    if len(tipos) < 3:
        return "Sin tendencia (pocos pivots válidos)"

    if tipos == ["L", "H", "L"] and valores[2] > valores[0]:
        return "Tendencia Bullish (mínimos ascendentes)"
    elif tipos == ["H", "L", "H"] and valores[2] < valores[0]:
        return "Tendencia Bearish (máximos descendentes)"
    else:
        return "Sin tendencia clara"


def graficar_pivots(df, symbol="Activo"):
    import plotly.io as pio
    import webbrowser
    import tempfile
    import os

    # Forzar renderer a browser para mayor fiabilidad
    pio.renderers.default = "browser"

    # Copia y limpieza de datos OHLC
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    for c in ['Open', 'High', 'Low', 'Close']:
        data[c] = pd.to_numeric(data[c], errors='coerce')
    data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    tendencia = determinar_tendencia(df)

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Precio'
    )])

    # Pivots High
    df_highs = data.loc[df.index[df['pivot_high']]] if 'pivot_high' in df.columns else data.iloc[0:0]
    if not df_highs.empty:
        fig.add_trace(go.Scatter(
            x=df_highs.index,
            y=df_highs['High'],
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
            y=df_lows['Low'],
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


# === Ejemplo de uso ===
if __name__ == "__main__":
    symbol = "6EZ25.CME"
    data = yf.download(symbol, period="6mo", interval="1d", multi_level_index=False)

    # Detectar pivots
    df_pivots = identificar_pivots(data, n=2)

    # Limpiar pivots redundantes
    df_pivots = limpiar_pivots(df_pivots)

    # Graficar resultado final
    graficar_pivots(df_pivots, symbol)
