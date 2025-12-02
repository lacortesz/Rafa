## ----- Rafa Main Script -----

## Import libraries
import pandas as pd
import yfinance as yf
import utils
import parameters   
import os
import subprocess
import sys


## Variables definition

## 1 Make premarket analysis
## 1.1 check if there are any assests with the three major timeframes aligned


## 2. create watchlist of assets with aligned timeframes

## 3. scan watchlist for entry signals

## 4. if there are entry signals, check if create order conditions are met
## 4.1 check if the market is open
## 4.2 check if there is a related news event in the next 20 minutes (parametizable)
## 4.3 check if there is an open position   
## 4.4 check if RSI is not overbought/oversold


## 5. if order conditions are met, create order
## 5.1 set stop loss and take profit levels

## manage open positions
## 6.1 check if there are any open positions
## 6.2 check if any open positions need to be closed



if __name__ == "__main__":

    info = pd.DataFrame()

    for name, symbol in parameters.symbols.items():
        for intervalo, periodo in parameters.intervalos_.items():
            print(f"Procesando {name} ({symbol}) para intervalo {intervalo} y periodo {periodo}")
            #symbol = parameters.symbols['Euro FX']
            #data = utils.download_data(symbol, '2024-06-01', '2024-06-20', '1d')
            data = yf.download(symbol, period=periodo, interval=intervalo, multi_level_index=False)

            data = utils.format_datetime_index(data, inplace=True)

            #print(data['DatetimeStr'])

            #adicionar indicadores tecnicos
            utils.adicionar_indicadores(data)

            print(f"Datos descargados para {name} ({symbol}):")
            print(data.tail(10))

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
                'Timeframe': intervalo,
                'Tendencia': tendencia,
                'RSI': rsi,
                'Soportes': soportes,
                'Resistencias': resistencias
            }, ignore_index=True)

            print(info.tail())

            #utils.graficar_pivots_soportes_resistencias(data, df_pivots, soportes, resistencias, symbol, tendencia, rsi, name=name, timeframe=intervalo)

    info.to_csv('info.csv', index=False)

    # Ejecutar web_table.py al finalizar
    print("\nIniciando servidor web en http://127.0.0.1:5000...")
    try:
        subprocess.Popen([sys.executable, 'web_table.py'], 
                         cwd=os.getcwd(),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        print("Servidor web iniciado. Abre http://127.0.0.1:5000 en tu navegador.")
    except Exception as e:
        print(f"Error al iniciar web_table.py: {e}")
        print("Ejecuta manualmente: python web_table.py")

    print("Info saved to info.csv")