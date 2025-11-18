import os
from flask import Flask, render_template_string, send_file
import pandas as pd

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Resumen Tendencias</title>
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
  </style>
</head>
<body>
  <h2>Resumen: Tendencia por Timeframe</h2>
  {% if table_html %}
    {{ table_html | safe }}
  {% else %}
    <p>No hay datos. Ejecuta rafa_main.py para generar <code>info.csv</code>.</p>
  {% endif %}
  <p class="small">Archivo: {{ path }}</p>
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

    if symbol_col is None or timeframe_col is None or trend_col is None:
        html = df.to_html(classes="table table-striped", index=False, escape=False)
        return render_template_string(HTML_TEMPLATE, table_html=html, path=path)

    # pivot: una fila por instrumento, columnas = timeframes
    pivot = df[[symbol_col, timeframe_col, trend_col]].dropna(subset=[symbol_col, timeframe_col])
    pivot_table = pivot.pivot_table(index=symbol_col, columns=timeframe_col, values=trend_col, aggfunc='first')
    pivot_table = pivot_table.fillna("")

    # normalizar nombres de columnas y construir mapeo normalizado -> original
    orig_cols = list(pivot_table.columns)
    norm_to_orig = {}
    for c in orig_cols:
        norm = str(c).strip().lower().replace(" ", "")
        norm_to_orig[norm] = c

    # ordenar columnas en el orden deseado (izquierda -> derecha)
    desired_order_norm = ['1d', '4h', '1h', '15m']
    cols_present = [norm_to_orig[n] for n in desired_order_norm if n in norm_to_orig]
    other_cols = [c for c in orig_cols if c not in cols_present]
    ordered_cols = cols_present + other_cols
    pivot_table = pivot_table.loc[:, ordered_cols] if ordered_cols else pivot_table

    # aplicar coloreado a cada celda (devuelve HTML en celda)
    styled = pivot_table.applymap(_colorize_trend)

    # generar HTML: convertir índice (símbolo) en columna para mostrar como primera columna
    styled = styled.reset_index()
    table_html = styled.to_html(index=False, escape=False, classes="table table-striped")

    return render_template_string(HTML_TEMPLATE, table_html=table_html, path=path)

@app.route("/download")
def download():
    path = os.path.join(os.getcwd(), "info.csv")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "info.csv not found", 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)