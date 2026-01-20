import nltk
import config
from newsapi import NewsApiClient
from textblob import TextBlob
from datetime import datetime, timedelta

nltk.download('punkt')

# =========================
# CONFIGURACIÓN
# =========================
NEWS_API_KEY = config.API_KEY
QUERY = "Crude Oil futures"  # Cambia por NQ futures, Gold futures, etc.
LANGUAGE = "en"
DAYS_BACK = 1

# Umbrales de decisión
BULLISH_THRESHOLD = 0.05
BEARISH_THRESHOLD = -0.05

# =========================
# INICIALIZAR CLIENTE
# =========================
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

# =========================
# OBTENER NOTICIAS
# =========================


def data_range(back_days):
    from_date = (datetime.utcnow() - timedelta(days=back_days)).strftime('%Y-%m-%d')
    return from_date

for symbol, fullname in config.simbols_fullname.items():
    #print(f"Analizando noticias para: {symbol}")

    back_days = 1
    from_date = data_range(back_days)
    
    temp = True

    while temp:
        try:
            articles = newsapi.get_everything(
                q=f"{fullname}",
                from_param=from_date,
                language=LANGUAGE,
                sort_by='relevancy',
                page_size=100
            )['articles']

        except Exception as e:
            print(f"Error al obtener noticias para {symbol}: {e}. Reintentando...")
    
        if not articles:
            print(f"No se encontraron noticias para el activo {symbol}")
            back_days += 1
            from_date = data_range(back_days)
        else:
            temp = False

    # =========================
    # ANALISIS DE SENTIMIENTO
    # =========================
    sentiments = []

    for article in articles:
        text = f"{article['title']} {article.get('description', '')}"
        polarity = TextBlob(text).sentiment.polarity
        sentiments.append(polarity)

    average_sentiment = sum(sentiments) / len(sentiments)

    # =========================
    # CLASIFICACIÓN DE TENDENCIA
    # =========================
    if average_sentiment > BULLISH_THRESHOLD:
        trend = "ALCISTA 📈"
    elif average_sentiment < BEARISH_THRESHOLD:
        trend = "BAJISTA 📉"
    else:
        trend = "SIN TENDENCIA ➖"

    # =========================
    # RESULTADO
    # =========================
    """print("Activo:", symbol)
    print("Noticias analizadas:", len(sentiments))
    print("Sentimiento promedio:", round(average_sentiment, 4))
    print("Tendencia inferida:", trend)
    print("----------------------")"""

    print(f"Activo {symbol} {fullname}, Tendencia: {trend}, No Noticias: {len(sentiments)}, Sentimiento Promedio: {round(average_sentiment, 4)}")



def get_market_sentiment(symbol):
    articles = newsapi.get_everything(
        q=f"{config.simbols_fullname.get(symbol, symbol)}",
        from_param=from_date,
        language=LANGUAGE,
        sort_by='relevancy',
        page_size=100
    )['articles']

    if not articles:
        raise ValueError("No se encontraron noticias para el activo")

    sentiments = []

    return sentiments

