import yfinance as yf
import pandas as pd
import utils    
import parameters
import plotly.graph_objects as go

info = pd.DataFrame()

'''def graficar(data, name, symbol, intervalo, periodo, timeframe):
    
    data = yf.download("CL=F", period="3d", interval="15M", multi_level_index=False)
    fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Precio'
    )])
    fig.update_layout(
        title = f"{name} ({symbol}) {timeframe} - intervalo {intervalo} periodo {periodo}",
        yaxis_title='Precio',
        xaxis_title='Fecha',
        template='plotly_white',
        xaxis_rangeslider_visible=False
    )
    fig.show()'

def graficar2():
    data = yf.download("CL=F", period="3d", interval="15M", multi_level_index=False)
    fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Precio'
    )])

    print(data.index)

    fig.update_layout(
        title = "CL=F - 15m - 3d",
        yaxis_title='Precio',
        xaxis_title='Fecha',
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        xaxis_type='category'
    )
    fig.show()

graficar2()'''


for name, symbol in parameters.symbols.items():
    for intervalo, periodo in parameters.intervalos.items():
        #print(f"Descargando datos para {name} ({symbol}) en intervalo {interval}:")
        print(f"Datos para {name} ({symbol}) en intervalo {intervalo} para el periodo {periodo}:")
        data = yf.download(symbol, period=periodo, interval=intervalo, multi_level_index=False)
        utils.adicionar_indicadores(data)
        #print(f"Datos descargados para {symbol}:")
        
        utils.adicionar_indicadores(data)

        # Detectar pivots
        df_pivots = utils.identificar_pivots(data, parameters.pivotStrength)

        # Detectar soportes y resistencias
        soportes, resistencias = utils.identificar_soportes_resistencias(data, window=10, tolerance=0.005, top_n=parameters.n_soportes_resistencias)

        # Graficar resultado final
        #utils.graficar_pivots(df_pivots, symbol)

        tendencia = utils.determinar_tendencia(df_pivots, parameters.trendStrength)
        rsi = utils.calcular_rsi(data['Close'], period=14)

        info = info._append({
            #'Nombre': name,
            'Símbolo': symbol,
            'Tendencia': tendencia,
            'RSI': rsi,
            'Soportes': soportes,
            'Resistencias': resistencias
        }, ignore_index=True)

        utils.graficar_pivots_soportes_resistencias(data, df_pivots, soportes, resistencias, symbol, tendencia, rsi, name=name, timeframe=intervalo)


        
        #print(data)
        #print(data.tail(30))
        #print(f"velas:  {len(data)}")
        #graficar(data, name, symbol, intervalo, periodo, timeframe=intervalo)


    