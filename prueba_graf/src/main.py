import utility.utility as utility
import pandas as pd

if __name__ == "__main__":

    df = utility.csv_to_pd("6A_15m")
    df = utility.normalize_data_types(df)

    #df_pivots = utility.identificar_pivots(df, 2)
    #print(df_pivots.tail(10))

    df = utility.identificar_pivots(df, 2)

    soportes, resistencias = utility.identificar_soportes_resistencias(df, window=10, tolerance=0.005, top_n=5)

    #tendencia = utility.determinar_tendencia(df_pivots, 2)
    tendencia = utility.determinar_tendencia(df, 3)

    rsi = utility.calcular_rsi(df['close'], period=14)

    utility.adicionar_indicadores(df)

    df = df.sort_index().tail(80)
    #df_pivots = df_pivots.sort_index().tail(80)

    print("df:")
    print(df.tail(10))
    #print("df_pivots:") 
    #print(df_pivots.tail(10))

    #utility.graficar_pivots_soportes_resistencias(df, df_pivots, soportes, resistencias, "6A", tendencia, rsi, name="6A", timeframe="15m")
    utility.graficar_pivots_soportes_resistencias_2(df, soportes, resistencias, "6A", tendencia, rsi, name="6A", timeframe="15m")