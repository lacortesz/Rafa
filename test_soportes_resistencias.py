# ...existing code...
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.signal import argrelextrema

def identificar_soportes_resistencias(df, window=10, tolerance=0.005, top_n=2):
    """
    Identifica niveles de soporte y resistencia y devuelve los top_n más
    cercanos al precio actual (último Close).

    Parámetros:
        df : pd.DataFrame con columnas ['High','Low','Close']
        window : int para argrelextrema
        tolerance : float para agrupar niveles muy cercanos (proporcional)
        top_n : int número de niveles por tipo a devolver (por defecto 2)
    Retorna:
        soportes_sel, resistencias_sel : listas con hasta top_n niveles (float)
    """
    data = df.copy()
    data = data.dropna(subset=['High','Low','Close'])
    if data.empty:
        return [], []

    highs_idx = argrelextrema(data['High'].values, np.greater_equal, order=window)[0]
    lows_idx = argrelextrema(data['Low'].values, np.less_equal, order=window)[0]

    pivote_highs = data['High'].iloc[highs_idx].values.tolist()
    pivote_lows = data['Low'].iloc[lows_idx].values.tolist()

    def agrupar_niveles(niveles):
        niveles = sorted(set(niveles))
        if not niveles:
            return []
        grupos = [niveles[0]]
        for nivel in niveles[1:]:
            if abs(nivel - grupos[-1]) / grupos[-1] > tolerance:
                grupos.append(nivel)
            else:
                # merge simple: promediar
                grupos[-1] = (grupos[-1] + nivel) / 2.0
        return grupos

    resistencias = agrupar_niveles(pivote_highs)
    soportes = agrupar_niveles(pivote_lows)

    # seleccionar los top_n más cercanos al precio actual (último close)
    precio_actual = float(data['Close'].iloc[-1])
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

def graficar_soportes_resistencias_plotly(df, soportes, resistencias, titulo="Soportes y Resistencias", symbol="Activo"):
    """
    Grafica velas con Plotly y dibuja líneas horizontales para soportes/resistencias.
    """
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    data = data.dropna(subset=['Open','High','Low','Close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
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

if __name__ == "__main__":
    import yfinance as yf

    symbol = "AAPL"
    data = yf.download(symbol, period="6mo", interval="1d", multi_level_index=False)
    top_n = 2  # por defecto
    soportes, resistencias = identificar_soportes_resistencias(data, window=10, tolerance=0.005, top_n=top_n)
    print("Soportes:", soportes)
    print("Resistencias:", resistencias)
    graficar_soportes_resistencias_plotly(data, soportes, resistencias, titulo=f"Soportes y Resistencias de {symbol}", symbol=symbol)
# ...existing code...