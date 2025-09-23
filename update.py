import yfinance as yf
import mplfinance as mpf
import pandas as pd
import time
from datetime import datetime, timedelta
import matplotlib.animation as animation     



def date_plus_days(date_str, days):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


# --- Configuración ---
symbol = "6EZ25.CME"   # símbolo del futuro
start_date = "2025-09-01"
end_date = date_plus_days(start_date, 1)  # fecha de fin inicial
interval = "1d"        # intervalo de las velas
refresh = 10           # en segundos, chequea cada 1 min

last_timestamp = None

# DataFrame acumulado
df_total = pd.DataFrame()
last_timestamp = None

if __name__ == "__main__": 

    while True:
        # Descargar desde el inicio hasta hoy
        df = yf.download(symbol, end=end_date, interval=interval, progress=False, multi_level_index=False)
        df = df.dropna()

        if not df.empty:
            new_last = df.index[-1]

            # Solo si hay vela nueva
            if new_last != last_timestamp:
                last_timestamp = new_last

                # Actualizar acumulado
                df_total = df.copy()

                print(f"📈 Nueva vela detectada: {last_timestamp.date()}")

                # Graficar todo el histórico acumulado
                mpf.plot(
                    df_total,
                    type="candle",
                    style="charles",
                    title=f"{symbol} - Velas diarias",
                    volume=True,
                    show_nontrading=False
                )
         
                #start_date = date_plus_days(start_date, 2)        
                end_date = date_plus_days(end_date, 1)

                print(df_total)

            #ani = 
        

        # Espera antes de volver a consultar
        time.sleep(refresh)


