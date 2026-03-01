# routes/dashboard.py
from flask import Blueprint, render_template
import pandas as pd
from urllib.parse import quote_plus

from utils.database import load_trend_data
from utils.dashboard import build_trend_table_html 

bp = Blueprint("dashboard", __name__)

@bp.route("/")
def index():
    """Render the dashboard with trend data.    
    return render_dashboard()
    """
    df = load_trend_data()
    if df.empty:
        return render_template("dashboard.html", table=None)

    desired_timeframes = ["1d", "240m", "60m", "15m"]

    pivot = (
        df.pivot(index="simbolo", columns="timeframe", values="tendencia")
        .reindex(columns=desired_timeframes)
        .fillna("")
    )

    market_240m = (
        df[df["timeframe"] == "240m"]
        .set_index("simbolo")["market"]
    )

    rsi_15m = (
        df[df["timeframe"] == "15m"]
        .set_index("simbolo")["rsi"]
    )

    pivot["market"] = market_240m
    pivot["rsi"] = rsi_15m
    

    pivot_html = build_trend_table_html(pivot)

    return render_template(
        "dashboard.html",
        table=pivot_html,
        quote=quote_plus,
        updated_at=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    )
