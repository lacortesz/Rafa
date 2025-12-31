#symbols = ["6EZ25.CME"]
import pandas as pd


n_soportes_resistencias = 2
tolerance = 0.005  # 0.5%
news_check_minutes = 20
pivotStrength = 2
trendStrength = 3

OUT_DIR = r"C:\repo_luis\Rafa\received_data"

symbols = {
    "E-mini S&P 500": "ES=F",
    "E-mini Nasdaq 100": "NQ=F",
    "E-mini Dow Jones": "YM=F",
    "Crudo WTI": "CL=F",
   "Oro": "GC=F",
    "Gas Natural": "NG=F",
    "Plata": "SI=F",
    "Cobre": "HG=F",
    "Maíz": "ZC=F",
    "Soya": "ZS=F",
    "Trigo": "ZW=F",
    "Euro FX": "6E=F",
    "Yen Japonés": "6J=F",
    "Libra Esterlina": "6B=F",
    "Dólar Australiano": "6A=F",
    "10-Year T-Note": "ZN=F"#,
    #"30-Year T-Bond": "ZB=F"
 
}

'''
    ,
    "E-mini Nasdaq 100": "NQ=F",
    "E-mini Dow Jones": "YM=F",
    "Crudo WTI": "CL=F",
   "Oro": "GC=F",
    "Gas Natural": "NG=F",
    "Plata": "SI=F",
    "Cobre": "HG=F",
    "Maíz": "ZC=F",
    "Soya": "ZS=F",
    "Trigo": "ZW=F",
    "Euro FX": "6E=F",
    "Yen Japonés": "6J=F",
    "Libra Esterlina": "6B=F",
    "Dólar Australiano": "6A=F",
    "10-Year T-Note": "ZN=F",
    "30-Year T-Bond": "ZB=F"
'''

#interval:period
intervalos = {
    '15m': '3d',
}


intervalos_ = {
    '1d': '6mo',
    '4h': '1mo',
    '1h': '1wk',
    '15m': '3d'
}

