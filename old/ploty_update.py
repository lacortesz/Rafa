import yfinance as yf
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# --- Configuración ---
symbol = "AAPL"          # Cambia por tu símbolo
interval = "5m"          # Velas de 5 minutos
period = "1d"            # Cuántos días hacia atrás (máx 7 días para 1m en Yahoo)

# --- Crear la app Dash ---
app = dash.Dash(__name__)
app.title = f"Gráfico en vivo {symbol}"

app.layout = html.Div([
    html.H2(f"Gráfico en vivo {symbol} - velas 1m"),
    dcc.Graph(id="candlestick-graph"),
    dcc.Interval(
        id="interval-component",
        interval=30*1000,  # refresca cada 30 segundos
        n_intervals=0
    )
])

# --- Callback para actualizar gráfico ---
@app.callback(
    Output("candlestick-graph", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_graph(n):
    # Descargar últimas velas
    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        progress=False,
        multi_level_index=False
    )
    df = df.dropna()

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
        title=f"{symbol} - Velas {interval}",
        xaxis_title="Hora",
        yaxis_title="Precio",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        autosize=True
    )

    return fig

# --- Ejecutar servidor ---
if __name__ == "__main__":
    app.run(debug=True)

'''df = yf.download(
    "AAPL",
    period="5d",
    interval="1m",
    progress=False
)
print(df.head())
print(df.tail())'''
