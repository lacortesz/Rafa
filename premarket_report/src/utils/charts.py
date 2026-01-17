# services/charts.py
import pandas as pd
import plotly.graph_objects as go
import os
import utils.parameters as parameters
import tempfile

def plot_pivots(df: pd.DataFrame, symbol: str) -> str:
    """
    Generates a candlestick chart with pivot points.
    Returns HTML.
    """
    data = df.copy()
    data.index = pd.to_datetime(data.index)

    for col in ("open", "high", "low", "close"):
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(subset=["open", "high", "low", "close"])
    if data.empty:
        return "<p>No OHLC data available.</p>"

    fig = go.Figure(go.Candlestick(
        x=data.index,
        open=data["open"],
        high=data["high"],
        low=data["low"],
        close=data["close"],
        name="Price"
    ))

    if "pivot_high" in data.columns:
        pivots = data[data["pivot_high"]]
        fig.add_scatter(
            x=pivots.index,
            y=pivots["high"],
            mode="markers",
            name="Pivot High"
        )

    if "pivot_low" in data.columns:
        pivots = data[data["pivot_low"]]
        fig.add_scatter(
            x=pivots.index,
            y=pivots["low"],
            mode="markers",
            name="Pivot Low"
        )

    fig.update_layout(
        title=f"Pivots – {symbol}",
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        height=700
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")

def load_bars_csv(symbol, timeframe, out_dir=None):
    """
    Carga el CSV correspondiente a (symbol, timeframe) desde out_dir y
    normaliza la columna 'datetime' y las columnas OHLC.
    Devuelve DataFrame con columna 'datetime' (datetime64) y columnas open/high/low/close (numéricas).
    """
    if out_dir is None:
        #out_dir = os.path.join(parameters.OUT_DIR_2)
        out_dir = os.path.join(parameters.OUT_DIR)
    filename = f"{symbol}_{timeframe}.csv"
    path = os.path.join(out_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_csv(path)
    # detectar/normalizar datetime
    datetime_cols = [c for c in df.columns if c.lower() in ("datetime", "time", "timestamp", "date")]
    if not datetime_cols:
        raise ValueError("No datetime column found in CSV")
    dt_col = datetime_cols[0]
    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
    df = df.sort_values(by=dt_col).reset_index(drop=True)
    if dt_col != "datetime":
        df = df.rename(columns={dt_col: "datetime"})

    # asegurar OHLC como numéricos
    for c in ("open", "high", "low", "close"):
        if c in df.columns:
            # intentar conversión numérica; si fallan (p.ej. "0,6695" con coma decimal), reemplazar comas por puntos
            s = df[c]
            df[c] = pd.to_numeric(s, errors="coerce")
            if df[c].isna().all():
                s2 = s.astype(str).str.replace(",", ".", regex=False)
                df[c] = pd.to_numeric(s2, errors="coerce")
        else:
            raise ValueError(f"Missing required column '{c}' in CSV {path}")

    return df

# utils/charts.py
def create_chart(df, soportes, resistencias, symbol="Activo", tendencia="", rsi=0,
                 sma_fast_col='SMA_FAST', sma_slow_col='SMA_SLOW', timeframe="1D"):
    """
    Plot pivots, supports and resistances in a single chart.
    """
    data = df.copy()
    
    # Set datetime index properly
    if 'datetime' in data.columns:
        data = data.set_index('datetime')
    data.index = pd.to_datetime(data.index)
    
    # Ensure OHLC columns are numeric
    for c in ['open', 'high', 'low', 'close']:
        if c in data.columns:
            data[c] = pd.to_numeric(data[c], errors='coerce')
    
    if data.empty:
        return "<p>No hay datos OHLC completos para graficar.</p>"

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Precio'
    )])

    # Pivot highs
    if 'pivot_high' in data.columns:
        df_highs = data[data['pivot_high'] == True]
        if not df_highs.empty:
            fig.add_trace(go.Scatter(
                x=df_highs.index,
                y=df_highs['high'],
                mode='markers+text',
                marker=dict(color='red', size=10),
                text=df_highs.get('pivot_label', ''),
                textposition='top center',
                name='Pivots High'
            ))

    # Pivot lows
    if 'pivot_low' in data.columns:
        df_lows = data[data['pivot_low'] == True]
        if not df_lows.empty:
            fig.add_trace(go.Scatter(
                x=df_lows.index,
                y=df_lows['low'],
                mode='markers+text',
                marker=dict(color='green', size=10),
                text=df_lows.get('pivot_label', ''),
                textposition='bottom center',
                name='Pivots Low'
            ))

    # Plot supports
    if soportes is not None and len(soportes) > 0:
        for i, nivel in enumerate(soportes):
            fig.add_trace(go.Scatter(
                x=[data.index[0], data.index[-1]],
                y=[nivel, nivel],
                mode='lines',
                line=dict(color='green', width=1.5, dash='dash'),
                name=f"Soporte {i+1}"
            ))

    # Plot resistances
    if resistencias is not None and len(resistencias) > 0:
        for i, nivel in enumerate(resistencias):
            fig.add_trace(go.Scatter(
                x=[data.index[0], data.index[-1]],
                y=[nivel, nivel],
                mode='lines',
                line=dict(color='red', width=1.5, dash='dash'),
                name=f"Resistencia {i+1}"
            ))

    # Add SMAs if they exist
    if sma_fast_col in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=pd.to_numeric(data[sma_fast_col], errors='coerce'),
            mode='lines',
            name=sma_fast_col,
            line=dict(color='orange', width=1.5)
        ))
    if sma_slow_col in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index,
            y=pd.to_numeric(data[sma_slow_col], errors='coerce'),
            mode='lines',
            name=sma_slow_col,
            line=dict(color='blue', width=1.5)
        ))

    # Get RSI value
    rsi_value = ""
    if 'RSI_14' in data.columns:
        last_rsi = pd.to_numeric(data['RSI_14'].iloc[-1], errors='coerce')
        if pd.notna(last_rsi):
            rsi_value = f"{last_rsi:.2f}"

    fig.update_layout(
        title=f"{symbol} {timeframe} - Trend: {tendencia} - RSI: {rsi_value}",
        yaxis_title='Price',
        yaxis=dict(automargin=True),
        xaxis=dict(
            tickangle=-45,
            tickmode='auto',
            tickfont=dict(size=10),
            rangeslider=dict(visible=False)
        ),
        template='plotly_white',
        width=1200,
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')

    """try:
        fig.show()
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), f"pivots_soportes_resistencias_{symbol}.html")
        fig.write_html(tmp, auto_open=True)"""