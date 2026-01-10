import yfinance as yf
import pandas as pd
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
TICKER = "6B=F"  # Puedes cambiarlo a otro símbolo, por ejemplo "MSFT", "GOOG", "TSLA"
REFRESH_INTERVAL = 30 * 1000  # tiempo de actualización en milisegundos (30s)

# --- FUNCIÓN PARA OBTENER DATOS ---
def get_data():
    df = yf.download(TICKER, period="1d", interval="1m", multi_level_index=False)  # datos del día actual con velas de 1 minuto
    df.reset_index(inplace=True)
    
    df["SMA14"] = df["Close"].rolling(window=14).mean()
    df["SMA20"] = df["Close"].rolling(window=20).mean()
    
    df =df.tail(60)  # mantener solo las últimas 60 filas (última hora)
    return df

# --- INICIALIZAR DASH ---
app = Dash(__name__)
app.title = f"Gráfico en tiempo real: {TICKER}"

# --- DISEÑO ---
app.layout = html.Div([
    html.H2(f"Gráfico de Velas - {TICKER}", style={'textAlign': 'center'}),
    dcc.Graph(id='candlestick-graph'),
    dcc.Interval(
        id='interval-component',
        interval=REFRESH_INTERVAL,  # actualización cada 30s
        n_intervals=0
    )
])

# --- CALLBACK PARA ACTUALIZAR GRÁFICO ---
@app.callback(
    Output('candlestick-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    df = get_data()

    fig = go.Figure(data=[go.Candlestick(
        x=df['Datetime'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=TICKER
    )])

    # SMA 14
    fig.add_trace(go.Scatter(
        x=df['Datetime'],
        y=df['SMA14'],
        mode='lines',
        line=dict(width=1.5, color='orange'),
        name='SMA 14'
    ))

    # SMA 20
    fig.add_trace(go.Scatter(
        x=df['Datetime'],
        y=df['SMA20'],
        mode='lines',
        line=dict(width=1.5, color='cyan'),
        name='SMA 20'
    ))


    fig.update_layout(
        title=f"{TICKER} - Actualización en tiempo real ({len(df)} puntos)",
        xaxis_title="Hora",
        yaxis_title="Precio (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    return fig

# --- EJECUTAR APLICACIÓN ---
if __name__ == '__main__':
    app.run(debug=True)
