# routes/chart.py
import os
from flask import Blueprint, render_template, request
import pandas as pd
from urllib.parse import unquote_plus
from utils.charts import create_chart, load_bars_csv
from utils.database import load_chart_data
from config import DATA_DIR


bp = Blueprint("chart", __name__)

@bp.route("/chart")
def chart():
    """Render chart for given symbol and timeframe.
    """

    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe")
    if not symbol or not timeframe:
        return "Please provide symbol and timeframe query params", 400
    
    # unquote in case values were encoded twice
    symbol = unquote_plus(symbol)
    timeframe = unquote_plus(timeframe)
    out_dir = os.path.join(DATA_DIR)

    try:
        df = load_bars_csv(symbol, timeframe, out_dir=out_dir)
    except FileNotFoundError:
        return f"CSV not found for {symbol} {timeframe}. Expected file: {out_dir}/{symbol}_{timeframe}.csv<br><a href='/'>Volver</a>"
    except Exception as e:
        return f"Error loading CSV: {e}<br><a href='/'>Volver</a>"

    # Load additional chart data from database
    chart_data = load_chart_data(symbol, timeframe)

    # Create chart with all data
    fig_html = create_chart(
        df,
        soportes=chart_data["soportes"],
        resistencias=chart_data["resistencias"],
        symbol=symbol,
        tendencia=chart_data["tendencia"],
        rsi=chart_data["rsi"],
        timeframe=timeframe,
    )
    
    return render_template(
        "chart.html",
        fig_html=fig_html,
        symbol=symbol,
        timeframe=timeframe
    )