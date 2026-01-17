# services/database.py
import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def load_trend_data() -> pd.DataFrame:
    """
    Loads trend and RSI data from PostgreSQL.
    """
    
    engine = create_engine(DATABASE_URL)

    query = """
        SELECT simbolo, timeframe, tendencia, rsi
        FROM info
    """

    with engine.begin() as conn:
        result = conn.execute(text(query))
        rows = result.fetchall()

    if not rows:
        print("⚠️ Query returned no rows")

    df = pd.DataFrame(
        rows,
        columns=["simbolo", "timeframe", "tendencia", "rsi"]
    )

    return df

def load_chart_data(symbol: str, timeframe: str):
    """
    Load trend, RSI, supports and resistances for a given symbol and timeframe.
    
    Returns:
        dict with keys: tendencia, rsi, soportes, resistencias
    """
    
    engine = create_engine(DATABASE_URL)

    query = """
            SELECT tendencia, rsi, soportes, resistencias 
            FROM info 
            WHERE simbolo = :symbol AND timeframe = :timeframe
    """

    try:
        with engine.begin() as conn:
            # Get trend and RSI
            result = conn.execute(
                text(query),
                {"symbol": symbol, "timeframe": timeframe}
            )
            row = result.fetchone()
            
            if row is None:
                return {
                    "tendencia": "",
                    "rsi": 0,
                    "soportes": None,
                    "resistencias": None
                }
            
            # Parse soportes/resistencias if stored as JSON/text
            soportes = parse_levels(row[2]) if row[2] else None
            resistencias = parse_levels(row[3]) if row[3] else None
            
            return {
                "tendencia": row[0] or "",
                "rsi": row[1] or 0,
                "soportes": soportes,
                "resistencias": resistencias
            }
    except Exception as e:
        print(f"Error loading chart data: {e}")
        return {
            "tendencia": "",
            "rsi": 0,
            "soportes": None,
            "resistencias": None
        }

def parse_levels(value):
    """
    Parse support/resistance levels from database.
    Handles JSON array or comma-separated string.
    """
    if not value:
        return None
    
    import json
    
    # If already a list
    if isinstance(value, list):
        return [float(x) for x in value]
    
    # Try JSON parse
    try:
        levels = json.loads(value)
        return [float(x) for x in levels]
    except:
        pass
    
    # Try comma-separated
    try:
        return [float(x.strip()) for x in str(value).split(',') if x.strip()]
    except:
        return None