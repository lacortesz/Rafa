import yfinance as yf
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# --- Configuración ---
symbol = "AAPL"           # símbolo a simular
start_date = "2025-09-19" # fecha inicial de la simulación
end_date = "2025-09-22"   # fecha final (opcional)
interval = "1m"           # velas de 1 minuto (puede ser 5m, 15m, 1h...)

# --- Descargar histórico completo ---
df_full = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False, multi_level_index=False)
df_full = df_full.dropna()

# --- Crear app Dash ---
app = dash.Dash(__name__)
app.title = f"Simulación {symbol}"

app.layout = html.Div([
    html.H2(f"Simulación de velas {interval} para {symbol} desde {start_date}"),
    dcc.Graph(id="candlestick-graph"),
    dcc.Interval(
        id="interval-component",
        interval=2000,   # refresca cada 2 segundos (simulación)
        n_intervals=0
    )
])

# --- Callback para actualizar gráfico ---
@app.callback(
    Output("candlestick-graph", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_graph(n):
    # Número de velas a mostrar en la simulación
    if n < 1:
        return go.Figure()

    # Cortar el DataFrame hasta la "vela n"
    df = df_full.iloc[:n]

    # Crear gráfico de velas
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Velas"
    )])

    fig.update_layout(
        title=f"{symbol} - Simulación hasta {df.index[-1]}",
        xaxis_title="Tiempo",
        yaxis_title="Precio",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    return fig

# --- Ejecutar servidor ---
if __name__ == "__main__":
    app.run(debug=True)
