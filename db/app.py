from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://admin:admin123@localhost:5432/trading_db"
)

with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO info (symbol, timeframe, price)
        VALUES (:s, :t, :p)
    """), {"s": "6B", "t": "1H", "p": 1.2345})
