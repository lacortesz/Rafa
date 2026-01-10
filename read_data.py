import utils.utils3 as utils3
import utils.utils4 as utils4
import  parameters
from pathlib import Path
import pandas as pd

DATA_DIR = Path(parameters.OUT_DIR)

dataframes = {}
data_pivots = {}
trends = {}
resistencias_soportes = {}

for file_path in DATA_DIR.glob("*.csv"):
    print(f"Procesando archivo: {file_path.name}")
    name = file_path.stem
    try:
        data = pd.read_csv(file_path, parse_dates=['datetime'], index_col='datetime')
        dataframes[name] = data
    except Exception as e:
        print(f"Error al procesar {file_path.name}: {e}")
        continue

    #data = utils.format_datetime_index(data, inplace=False)

    print(f"Datos procesados para {file_path.name}:")
    #print(data.head(5))

for name, data in dataframes.items():
    print(f"mostrando datos para {name}")
    print(dataframes[name].tail(5))
    #data_pivots[name] = utils3.identificar_pivots(dataframes[name], parameters.pivotStrength)
    #trends[name] = utils3.determinar_tendencia(data_pivots[name], parameters.trendStrength)
    #data_pivots = utils.identificar_pivots(data, parameters.pivotStrength)
    
    
    #deteminar tendencia
    trends[name] = utils4.get_trend(dataframes[name], parameters.pivotStrength, parameters.trendStrength)

with open('tendencias.csv', 'w') as f:
    for name in trends.keys():
        #soportes, resistencias = utils3.identificar_soportes_resistencias(
        #    dataframes[name],
        #    window=10,
        #    tolerance=parameters.tolerance,
        #    top_n=parameters.n_soportes_resistencias
        #)
        #resistencias_soportes[name] = (soportes, resistencias)
 
        print(f"Tendencia para {name}: {trends[name]}")
        f.write(f"{name},{trends[name]}\n")       
        #print(f"Soportes para {name}: {soportes}")
        #print(f"Resistencias para {name}: {resistencias}")

