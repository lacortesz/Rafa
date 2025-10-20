import yfinance as yf
import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
TICKER = "6B=F"
REFRESH_INTERVAL = 1 * 1000  # ms

# descargar datos una vez para simular la ejecución
start = pd.Timestamp.now() - pd.Timedelta(hours=6)
end = pd.Timestamp.now() 
start_str = start.strftime('%Y-%m-%d %H:%M:%S')
end_str = end.strftime('%Y-%m-%d %H:%M:%S')

print("Downloading data from", start_str, "to", end_str)
FULL_DF = yf.download(TICKER, start=start, end=end, interval="1m", progress=False, multi_level_index=False)
if FULL_DF.empty:
    print("No data downloaded. Revisa el ticker o la conexión.")
else:
    FULL_DF = FULL_DF.reset_index()
    FULL_DF["SMA14"] = FULL_DF["Close"].rolling(window=14).mean()
    FULL_DF["SMA20"] = FULL_DF["Close"].rolling(window=20).mean()
    print(f"Downloaded {len(FULL_DF)} rows")

WINDOW_SIZE = 60

# --- INICIALIZAR DASH ---
app = Dash(__name__)
app.title = f"Gráfico en tiempo real: {TICKER}"

app.layout = html.Div([
    html.H2(f"Simulación de Velas - {TICKER}", style={'textAlign': 'center'}),
    dcc.Graph(id='candlestick-graph'),
    dcc.Interval(
        id='interval-component',
        interval=REFRESH_INTERVAL,
        n_intervals=0
    )
], style={'height': '100vh', 'width': '100vw', 'margin': 0, 'padding': 0})

# --- CALLBACK PARA SIMULAR REPRODUCCIÓN ---
@app.callback(
    Output('candlestick-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    if FULL_DF.empty:
        fig = go.Figure()
        fig.update_layout(title="No hay datos para mostrar")
        return fig

    # calcular ventana móvil: empieza en 0-59 y avanza 1 vela por intervalo
    max_start = max(0, len(FULL_DF) - WINDOW_SIZE)
    start_idx = min(n, max_start)
    end_idx = start_idx + WINDOW_SIZE
    df_win = FULL_DF.iloc[start_idx:end_idx]

    fig = go.Figure(data=[go.Candlestick(
        x=df_win['Datetime'],
        open=df_win['Open'],
        high=df_win['High'],
        low=df_win['Low'],
        close=df_win['Close'],
        name=TICKER
    )])

    fig.add_trace(go.Scatter(
        x=df_win['Datetime'],
        y=df_win['SMA14'],
        mode='lines',
        line=dict(width=1.5, color='orange'),
        name='SMA 14'
    ))

    fig.add_trace(go.Scatter(
        x=df_win['Datetime'],
        y=df_win['SMA20'],
        mode='lines',
        line=dict(width=1.5, color='cyan'),
        name='SMA 20'
    ))

    current_range_end = df_win['Datetime'].iloc[-1] if not df_win.empty else None
    fig.update_layout(
        title=f"{TICKER} - Simulación (velas {start_idx + 1} a {end_idx} / {len(FULL_DF)}) - hasta {current_range_end}",
        xaxis_title="Hora",
        yaxis_title="Precio",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        autosize=True,
        margin=dict(l=40, r=20, t=60, b=40)
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)