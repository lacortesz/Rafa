import os
from flask import Flask, render_template_string, send_file, request
import pandas as pd
from urllib.parse import quote_plus, unquote_plus
import utils.utils3 as utils3
import plotly.io as pio
import plotly.graph_objects as go
import tempfile
import webbrowser

app = Flask(__name__)


HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Pre Market</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
    th { background-color: #f2f2f2; }
    tr:hover { background-color: #f9f9f9; }
    .small { font-size: 0.9em; color: #666; }
    .cell-bull { color: green; font-weight: 700; }
    .cell-bear { color: red; font-weight: 700; }
    .cell-none { color: #666; }
    a.cell-link { text-decoration: none; color: inherit; display:block; width:100%; height:100%; }
  </style>
</head>
<body>
  <h2>Resumen: Tendencia por Timeframe</h2>
  <p><a href="/tendencias">Ver tabla de tendencias desde <code>tendencias.csv</code></a></p>
  {% if table_html %}
    {{ table_html | safe }}
  {% else %}
    <p>No hay datos. Ejecuta <code>rafa_main.py</code> para generar <code>info.csv</code>.</p>
  {% endif %}
  <p class="small">Archivo: {{ path }}</p>
</body>
</html>
"""

CHART_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Chart - {{ symbol }} {{ timeframe }}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
  <h2>{{ symbol }} — {{ timeframe }}</h2>
  <p><a href="/">← Volver</a></p>
  <div>{{ fig_html | safe }}</div>
</body>
</html>
"""

def _find_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    cols_lower = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None

def _colorize_trend(val):
    if pd.isna(val) or str(val).strip() == "":
        return ""
    s = str(val).strip()
    low = s.lower()
    if "bull" in low or "alc" in low or "hh" in low:
        return f'<span class="cell-bull">{s}</span>'
    if "bear" in low or "baj" in low or "lh" in low:
        return f'<span class="cell-bear">{s}</span>'
    if "no" in low or "sin" in low:
        return f'<span class="cell-none">{s}</span>'
    return s

@app.route("/")
def index():
    path = os.path.join(os.getcwd(), "info.csv")
    if not os.path.exists(path):
        return render_template_string(HTML_TEMPLATE, table_html=None, path=path)

    df = pd.read_csv(path)

    symbol_col = _find_column(df, ['Símbolo', 'Simbolo', 'Symbol', 'Ticker', 'Name'])
    timeframe_col = _find_column(df, ['Timeframe', 'Intervalo', 'Interval', 'Period'])
    trend_col = _find_column(df, ['Tendencia', 'Trend', 'tendencia', 'Trend'])

    if symbol_col and timeframe_col and trend_col:
        pivot = df[[symbol_col, timeframe_col, trend_col]].dropna(subset=[symbol_col, timeframe_col])
        pivot_table = pivot.pivot_table(index=symbol_col, columns=timeframe_col, values=trend_col, aggfunc='first')
        pivot_table = pivot_table.fillna("")

        # Construir HTML con enlaces clicables en cada celda
        norm_index = list(pivot_table.index)
        cols = list(pivot_table.columns)

        html = ['<table>']
        # header
        html.append('<thead><tr><th>Symbol</th>')
        for c in cols:
            html.append(f'<th>{c}</th>')
        html.append('</tr></thead>')
        # body
        html.append('<tbody>')
        for sym in norm_index:
            html.append(f'<tr><td>{sym}</td>')
            for c in cols:
                cell_val = pivot_table.loc[sym, c]
                display_html = _colorize_trend(cell_val)
                # link target to chart route (encode params)
                sym_q = quote_plus(str(sym))
                tf_q = quote_plus(str(c))
                link = f'/chart?symbol={sym_q}&timeframe={tf_q}'
                cell_html = f'<a class="cell-link" href="{link}" target="_blank">{display_html or "–"}</a>'
                html.append(f'<td>{cell_html}</td>')
            html.append('</tr>')
        html.append('</tbody></table>')
        table_html = "\n".join(html)

        return render_template_string(HTML_TEMPLATE, table_html=table_html, path=path)

    # Fallback: mostrar tabla simple coloreada
    if symbol_col and symbol_col in df.columns:
        cols = [symbol_col] + [c for c in df.columns if c != symbol_col]
    else:
        cols = list(df.columns)

    df_display = df[cols].copy()
    if trend_col and trend_col in df_display.columns:
        df_display[trend_col] = df_display[trend_col].apply(_colorize_trend)

    table_html = df_display.to_html(index=False, escape=False, classes="table table-striped")
    return render_template_string(HTML_TEMPLATE, table_html=table_html, path=path)

@app.route("/tendencias")
def tendencias():
    path = os.path.join(os.getcwd(), "tendencias.csv")
    if not os.path.exists(path):
        return render_template_string(HTML_TEMPLATE, table_html=None, path=path)
    try:
        df = pd.read_csv(path, header=None, names=['name','trend'])
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, table_html=f"<p>Error leyendo {path}: {e}</p>", path=path)
    if df.empty:
        return render_template_string(HTML_TEMPLATE, table_html=None, path=path)

    # split name into instrument and timeframe by the first underscore
    split = df['name'].str.split('_', n=1, expand=True)
    df['instrument'] = split[0]
    df['timeframe'] = split[1]

    pivot_table = df.pivot_table(index='instrument', columns='timeframe', values='trend', aggfunc='first').fillna("")

    html = ['<table>']
    # header
    html.append('<thead><tr><th>Instrumento</th>')
    for c in pivot_table.columns:
        html.append(f'<th>{c}</th>')
    html.append('</tr></thead>')
    # body
    html.append('<tbody>')
    for sym in pivot_table.index:
        html.append(f'<tr><td>{sym}</td>')
        for c in pivot_table.columns:
            cell_val = pivot_table.loc[sym, c]
            display_html = _colorize_trend(cell_val)
            # link to chart route
            sym_q = quote_plus(str(sym))
            tf_q = quote_plus(str(c))
            link = f'/chart?symbol={sym_q}&timeframe={tf_q}'
            cell_html = f'<a class="cell-link" href="{link}" target="_blank">{display_html or "–"}</a>'
            html.append(f'<td>{cell_html}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    table_html = "\n".join(html)

    return render_template_string(HTML_TEMPLATE, table_html=table_html, path=path)


@app.route("/chart")
def chart():
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe")
    if not symbol or not timeframe:
        return "Please provide symbol and timeframe query params", 400
    # unquote in case values were encoded twice
    symbol = unquote_plus(symbol)
    timeframe = unquote_plus(timeframe)

    try:
        df = utils3.load_bars_csv(symbol, timeframe, out_dir=os.path.join(os.getcwd(), "received_data"))
    except FileNotFoundError:
        return f"CSV not found for {symbol} {timeframe}. Expected file: received_data/{symbol}_{timeframe}.csv<br><a href='/'>Volver</a>"
    except Exception as e:
        return f"Error loading CSV: {e}<br><a href='/'>Volver</a>"

    graficar_pivots(df, symbol)

@app.route("/download")
def download():
    path = os.path.join(os.getcwd(), "info.csv")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "info.csv not found", 404

def graficar_pivots(df, symbol="Activo"):

    # Forzar renderer a browser para mayor fiabilidad
    pio.renderers.default = "browser"

    # Copia y limpieza de datos OHLC
    data = df.copy()
    data.index = pd.to_datetime(data.index)
    for c in ['open', 'high', 'low', 'close']:
        data[c] = pd.to_numeric(data[c], errors='coerce')
    data = data.dropna(subset=['open', 'high', 'low', 'close'])
    if data.empty:
        print("No hay datos OHLC completos para graficar.")
        return

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        name='Precio'
    )])

    # Pivots High
    df_highs = data.loc[df.index[df['pivot_high']]] if 'pivot_high' in df.columns else data.iloc[0:0]
    if not df_highs.empty:
        fig.add_trace(go.Scatter(
            x=df_highs.index,
            y=df_highs['high'],
            mode='markers+text',
            marker=dict(color='red', size=10),
            text=df_highs.get('pivot_label', None),
            textposition='top center',
            name='Pivots High'
        ))

    # Pivots Low
    df_lows = data.loc[df.index[df['pivot_low']]] if 'pivot_low' in df.columns else data.iloc[0:0]
    if not df_lows.empty:
        fig.add_trace(go.Scatter(
            x=df_lows.index,
            y=df_lows['low'],
            mode='markers+text',
            marker=dict(color='green', size=10),
            text=df_lows.get('pivot_label', None),
            textposition='bottom center',
            name='Pivots Low'
        ))

    fig.update_layout(
        title=f"Pivots - {symbol}",
        yaxis_title='Precio',
        xaxis_title='Fecha',
        template='plotly_white',
        width=1200,
        height=700,
        xaxis_rangeslider_visible=False,
        xaxis_type='category',
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )

    # Mostrar; si falla, guardar HTML y abrir en navegador
    try:
        fig.show()
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), f"pivots_{symbol}.html")
        fig.write_html(tmp, auto_open=True)
        try:
            webbrowser.open(f"file://{tmp}")
        except Exception:
            print(f"Gráfica guardada en: {tmp}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)