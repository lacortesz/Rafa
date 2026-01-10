import yfinance as yf
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# --- Configuración ---
symbol = "AAPL"           # símbolo a simular
#start_date = "2025-09-19" # fecha inicial de la simulación
end_date = pd.Timestamp("2025-09-01")   # fecha inicial de descarga
interval = "1d"

# --- Descargar histórico inicial ---
df_full = yf.download(symbol, end=end_date, interval=interval, progress=False, multi_level_index=False)
df_full = df_full.dropna()

# --- Crear app Dash ---
app = dash.Dash(__name__)
app.title = f"Simulación {symbol}"

# Variables globales
current_end = end_date
today = pd.Timestamp.today().normalize()  # límite hasta hoy

app.layout = html.Div([
    #html.H2(f"Simulación de velas {interval} para {symbol} desde {start_date}"),
    html.H2(f"Simulación de velas {interval} para {symbol} hasta hoy"),
    dcc.Graph(id="candlestick-graph"),
    dcc.Interval(
        id="interval-component",
        interval=1000,   # refresca cada 1 segundo
        n_intervals=0
    )
])

# --- Callback para actualizar gráfico ---
@app.callback(
    [Output("candlestick-graph", "figure"),
     Output("interval-component", "disabled")],
    [Input("interval-component", "n_intervals")]
)
def update_graph(n):
    global current_end, df_full

    if n < 1:
        return go.Figure(), False

    disabled = False  # por defecto sigue activo

    # Avanzar solo si no hemos llegado a hoy
    if current_end < today:
        current_end = current_end + pd.Timedelta(days=1)
        df_full = yf.download(symbol, end=current_end, interval=interval, progress=False, multi_level_index=False)
        df_full = df_full.dropna()
        print(f"Actualizando hasta {current_end.strftime('%Y-%m-%d')}")
    else:
        print("Ya se alcanzó la fecha actual, mostrando gráfico final...")
        disabled = True  # desactiva Interval

    # Calcular SMA20
    df_full["SMA20"] = df_full["Close"].rolling(window=20).mean()

    print(df_full.tail(3))

    # Crear gráfico de velas
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_full.index,
        open=df_full["Open"],
        high=df_full["High"],
        low=df_full["Low"],
        close=df_full["Close"],
        name="Velas"
    ))

    # Añadir línea SMA20
    fig.add_trace(go.Scatter(
        x=df_full.index,
        y=df_full["SMA20"],
        mode="lines",
        line=dict(color="orange", width=2),
        name="SMA20"
    ))

    fig.update_layout(
        title=f"{symbol} - Simulación hasta {df_full.index[-1]}",
        xaxis_title="Tiempo",
        yaxis_title="Precio",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    return fig, disabled

# --- Ejecutar servidor ---
if __name__ == "__main__":
    app.run(debug=True)
