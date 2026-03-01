import nltk
import config
from newsapi import NewsApiClient
from textblob import TextBlob
from datetime import datetime, timedelta

def initialize_newsapi(api_key):
    """Initialize and return the NewsApiClient instance.
     return: NewsApiClient instance.
    """
    try:
        nltk.data.find("tokenizers/punkt")
        print("✅ 'punkt' ya está descargado")
    except LookupError:
        print("❌ 'punkt' no está descargado")
        nltk.download('punkt')
    
    newsapi = NewsApiClient(api_key=api_key)
    return newsapi

def data_range(back_days):
    """Calculate the date range for fetching news articles.
    param back_days: Number of days back from today.
    return: Date string in 'YYYY-MM-DD' format."""

    from_date = (datetime.utcnow() - timedelta(days=back_days)).strftime('%Y-%m-%d')
    return from_date

def get_articles(newsapi, symbol, from_date):
    """Fetch news articles and analyze their sentiment for a given symbol.
    parameters:
        newsapi: Initialized NewsApiClient instance.
        symbol: Financial instrument symbol.
        from_date: Date string to fetch articles from.
    return: List of articles.
    """

    articles = newsapi.get_everything(
        q=f"{config.symbols_fullname.get(symbol, symbol)}",
        from_param=from_date,
        language=config.LANGUAGE,
        sort_by='relevancy',
        page_size=100
    )['articles']

    return articles

def analyze_sentiment(articles):
    """Analyze sentiment of the provided articles.
    parameters:
        articles: List of news articles.
    return: 
        Tuple containing trend, average sentiment, and number of articles analyzed.
    """

    sentiments = []
    for article in articles:
        text = f"{article['title']} {article.get('description', '')}"
        polarity = TextBlob(text).sentiment.polarity
        sentiments.append(polarity)

    average_sentiment = sum(sentiments) / len(sentiments)

    # =========================
    # CLASIFICACIÓN DE TENDENCIA
    # =========================
    if average_sentiment > config.BULLISH_THRESHOLD:
        trend = "bullish"
    elif average_sentiment < config.BEARISH_THRESHOLD:
        trend = "bearish"
    else:
        trend = "flat"

    return trend, average_sentiment, len(sentiments)

def get_market_sentiment(symbol):
    
    newsapi = initialize_newsapi(config.NEWS_API_KEY)
    no_articles = True
    back_days = 1
    from_date = data_range(back_days)
    full_name = config.symbols_fullname.get(symbol, symbol)

    while no_articles:
        try:
            articles = get_articles(newsapi, full_name, from_date)

        except Exception as e:
            print(f"Error fetching articles for {symbol} {full_name}: {e}. Retrying...")
            return "error"
        
        if not articles:
            print(f"No articles found for {symbol} {full_name}")
            if back_days < 7:
                back_days += 1
                from_date = data_range(back_days)
            else:
                print(f"No articles found for {symbol} after checking 7 days. Exiting.")
                return "no_data"
        else:
            no_articles = False

    trend, average_sentiment, num_articles = analyze_sentiment(articles)

    print(f"Symbol: {symbol}, Trend: {trend}, Articles Analyzed: {num_articles}, Average Sentiment: {round(average_sentiment, 4)}")

    return trend 