import yfinance as yf
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd

# --- Configuración ---
symbol = "AAPL"           # símbolo a simular
start_date = "2025-09-19" # fecha inicial de la simulación
end_date = pd.Timestamp("2025-08-01")   # <--- convertir a Timestamp
interval = "1d"

# --- Descargar histórico completo ---
df_full = yf.download(symbol, end=end_date, interval=interval, progress=False, multi_level_index=False)
df_full = df_full.dropna()

# --- Crear app Dash ---
app = dash.Dash(__name__)
app.title = f"Simulación {symbol}"

# Variable global para ir avanzando un día
current_end = end_date

app.layout = html.Div([
    html.H2(f"Simulación de velas {interval} para {symbol} desde {start_date}"),
    dcc.Graph(id="candlestick-graph"),
    dcc.Interval(
        id="interval-component",
        interval=2000,   # refresca cada 2 segundos
        n_intervals=0
    )
])

# --- Callback para actualizar gráfico ---
@app.callback(
    Output("candlestick-graph", "figure"),
    [Input("interval-component", "n_intervals")]
)
def update_graph(n):
    global current_end

    if n < 1:
        return go.Figure()

    # avanzar un día en cada actualización
    current_end = current_end + pd.Timedelta(days=1)
    #current_end = current_end.strftime("%Y-%m-%d")
    
    # Descargar hasta la nueva fecha
    df_full = yf.download(symbol, end=current_end, interval=interval, progress=False, multi_level_index=False)
    df_full = df_full.dropna()
    print("Datos descargados:")
    print(df_full)

    print("Actualizando hasta", current_end)

    fig = go.Figure(data=[go.Candlestick(
        x=df_full.index,
        open=df_full["Open"],
        high=df_full["High"],
        low=df_full["Low"],
        close=df_full["Close"],
        name="Velas"
    )])

    fig.update_layout(
        title=f"{symbol} - Simulación hasta {df_full.index[-1]}",
        xaxis_title="Tiempo",
        yaxis_title="Precio",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    return fig

# --- Ejecutar servidor ---
if __name__ == "__main__":
    app.run(debug=True)
