import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

pivots = []

def get_trend(df, pivotTrendStrength=2, trendStrength=3):
    """
    Obtiene la tendencia del DataFrame df basado en pivots.
    parametros:
        df: DataFrame con datos OHLC    
        pivotTrendStrength: número de velas a considerar antes y después para identificar un pivot
        trendStrength: número de pivotes a considerar para determinar la tendencia  
    retorna:
        'bullish', 'bearish' o 'flat'
    """
    #llama funcion que identifica pivots
    pivots = get_pivots(df, pivotTrendStrength) 
    #limpia pivots consecutivos del mismo tipo
    pivots = clean_pivots(pivots)
    #clasifica pivots en HH, HL, LH, LL
    pivots = classify_pivots(pivots)

    #con los pivots clasificados, identifica la tendencia
    return identify_trend(df, pivots, trendStrength)

def plot_chart(df, instrument, timeframe, trend, pivots=None, soportes=None, resistencias=None):
    """
    Grafica el DataFrame df como un gráfico de velas.
    parametros:
        df: DataFrame con datos OHLC
        instrument: símbolo del instrumento financiero
        timeframe: intervalo de tiempo de las velas
        pivots: lista de pivots como diccionarios {'type': 'H' o 'L', 'index': index del DataFrame, 'value': valor del pivot} (opcional)
        soportes: lista de niveles de soporte (opcional)
        resistencias: lista de niveles de resistencia (opcional)
    retorna:
        None
    """
    title = f'{instrument} - {timeframe} - trend: {trend}'

    mpf.plot(df, type='candle', style='charles', title=title, volume=False)
    plt.show()


## Funciones auxiliares para get_trend

def get_pivots(df, pivotStrength=2):
    """
    Obtiene los pivots del DataFrame df.
    reglas:
    - Pivot high, el valor high de la vela es mayor al valor high de las n velas anteriores y posteriores
    - Pivot low, el valor low de la vela es menor al valor low de las n velas anteriores y posteriores
    parametros:
        df: DataFrame con datos OHLC
        pivotStrength: número de velas a considerar antes y después para identificar un pivot
    retorna:
        lista de pivots como diccionarios {'type': 'H' o 'L', 'index': index del DataFrame, 'value': valor del pivot}  
    """
    #lista para guardar pivots
    pivots=[]
    
    #Recorrer el DataFrame desde pivotStrength hasta len(df) - pivotStrength, es decir ignorando los primeros y últimos n valores
    for i in range(pivotStrength, len(df) - pivotStrength):
        #inicializar banderas en true
        is_pivot_high = True
        is_pivot_low = True

        #Guarda el high y low de la vela actual
        current_high = df['High'].iloc[i]
        current_low = df['Low'].iloc[i]

        #Recorre el rango pivotStrength velas antes y después de la vela actual
        for j in range(1, pivotStrength):
            if df['High'].iloc[i - j] >= current_high or df['High'].iloc[i + j] >= current_high: # 
                #Cambia la bandera a false si encuentra un high mayor o igual en las velas anteriores o posteriores
                is_pivot_high = False
            if df['Low'].iloc[i - j] <= current_low or df['Low'].iloc[i + j] <= current_low:
                #Cambia la bandera a false si encuentra un low menor o igual en las velas anteriores o posteriores
                is_pivot_low = False
            
        #guarda el pivot si alguna de las banderas sigue en true despues de la validación       
        if is_pivot_high:
            pivots.append({'type': 'H', 'index': df.index[i], 'value': current_high})
        if is_pivot_low:
            pivots.append({'type': 'L', 'index': df.index[i], 'value': current_low})

    return pivots

def clean_pivots(pivots):
    """
    Limpia la lista de pivots eliminando pivots consecutivos del mismo tipo.
    parametros:
        pivots: lista de pivots como diccionarios {'type': 'H' o 'L', 'index': index del DataFrame, 'value': valor del pivot}
    retorna:
        lista de pivots limpiada
    """
    cleaned = []
    for i, pivot in enumerate(pivots):
        if i == 0 or pivot['type'] != pivots[i-1]['type']:
            cleaned.append(pivot)
    return cleaned

def classify_pivots(pivots):
    """
    Clasifica los pivots en HH, HL, LH, LL.
    Reglas: 
    - HH: un pivot high mayor que el anterior pivot high
    - HL: un pivot low mayor que el anterior pivot low
    - LH: un pivot high menor que el anterior pivot high
    - LL: un pivot low menor que el anterior pivot low
    retorna:
        lista de pivots clasificados como diccionarios {'type': 'H' o 'L', 'type2': 'HH', 'HL', 'LH', 'LL', 'index': index del DataFrame, 'value': valor del pivot}
    """
    for i in range(2, len(pivots)):
        current = pivots[i]
        previous = pivots[i - 2]

        if current['type'] == 'H' and previous['type'] == 'H':
            if current['value'] > previous['value']:
                current['type2'] = 'HH'
            else:
                current['type2'] = 'LH'
        elif current['type'] == 'L' and previous['type'] == 'L':
            if current['value'] > previous['value']:
                current['type2'] = 'HL'
            else:
                current['type2'] = 'LL'

    df_pivots = pd.DataFrame(pivots)    
    print(df_pivots.tail(10))

    return pivots

   
def identify_trend(df, pivots, trendStrength=3):
    """
    Determina la tendencia basada en los últimos pivotes clasificados.
    Reglas:
    bullish: secuencia de HH y HL y el valor low de las velas siguientes al ultimo pivot HL son mayores al low del pivot HL
    bearish: secuencia de LL y LH y el valor high de las velas siguientes al ultimo pivot LH son menores al high del pivot LH
    flat: en cualquier otro caso
    parametros:
        df: DataFrame con datos OHLC
        pivots: lista de diccionarios con pivots clasificados
        trendStrength: número de pivotes a considerar para determinar la tendencia
    retorna:
        'bullish', 'bearish' o 'flat'
    """
    # si el numero de pivots es menor que trendStrength, retornar 'flat'. No hay suficiente info
    if len(pivots) < trendStrength:
        return "flat"
    
    # Obtener los últimos n pivots
    last_pivots = pivots[-trendStrength:]
    
    #validar secuencia bullish
    is_bullish = True
    for pivot in last_pivots:
        if pivot['type2'] not in ['HH', 'HL']:
            is_bullish = False
            break
    if is_bullish:
        # Buscar el último pivot con clasificación 'HL' entre los últimos pivotes. Se recorre en orden inverso (del más reciente al más antiguo) y se toma el primer pivot que cumpla la condición; si no hay ninguno, devuelve None.
        last_HL = next((p for p in reversed(last_pivots) if p['type2'] == 'HL'), None)
        if last_HL:
            # Toma la serie de mínimos ('low') desde la fila del pivot hasta el final.
            subsequent_lows = df.loc[last_HL['index']:]['Low'].iloc[1:]

            # Verifica que TODOS los mínimos posteriores sean estrictamente mayores que el valor del pivot. 
            if all(subsequent_lows >= last_HL['value']):
                # Si la condición se cumple, devuelve 'bullish'.
                return "bullish"

    #validar secuencia bearish
    is_bearish = True
    for pivot in last_pivots:
        if pivot['type2'] not in ['LL', 'LH']:
            is_bearish = False
            break       
    if is_bearish:
        # Buscar el último pivot con clasificación 'LH' entre los últimos pivotes. Se recorre en orden inverso (del más reciente al más antiguo) y se toma el primer pivot que cumpla la condición; si no hay ninguno, devuelve None.
        last_LH = next((p for p in reversed(last_pivots) if p['type2'] == 'LH'), None)
        if last_LH:
            # Toma la serie de máximos ('high') desde la fila del pivot hasta el final.
            subsequent_highs = df.loc[last_LH['index']:]['High'].iloc[1:]

            # Verifica que TODOS los máximos posteriores sean estrictamente menores que el valor del pivot. 
            if all(subsequent_highs <= last_LH['value']):
                # Si la condición se cumple, devuelve 'bearish'.
                return "bearish"    
    
    # Si ninguna de las condiciones anteriores se cumple, devuelve 'flat'.
    return "flat"