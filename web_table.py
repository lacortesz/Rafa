from flask import Flask, render_template_string, send_file
import pandas as pd
import os

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Tabla de Símbolos</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    tr:hover { background-color: #f9f9f9; }
    .small { font-size: 0.9em; color: #666; }
  </style>
</head>
<body>
  <h2>Resumen: Símbolo · Intervalo · Tendencia</h2>
  {% if df_html %}
    {{ df_html | safe }}
  {% else %}
    <p>No hay datos. Ejecuta rafa_main.py para generar <code>info.csv</code>.</p>
  {% endif %}
  <p class="small">Archivo: {{ path }}</p>
</body>
</html>
"""

@app.route("/")
def index():
    path = os.path.join(os.getcwd(), "info.csv")
    if not os.path.exists(path):
        return render_template_string(HTML_TEMPLATE, df_html=None, path=path)
    df = pd.read_csv(path)
    # Mostrar solo las columnas solicitadas (puedes ajustarlas)
    cols = [c for c in ['Símbolo', 'Timeframe', 'Tendencia'] if c in df.columns]
    # Si tu info no contiene "Intervalo", puedes mapearla antes o incluirla en rafa_main
    if 'Timeframe' not in df.columns and 'Soportes' in df.columns:
        # ejemplo: agregar columna intervalo vacía si no existe
        df['Timeframe'] = ''
        cols = ['Símbolo', 'Timeframe', 'Tendencia']
    df_disp = df[cols]
    html = df_disp.to_html(classes="table table-striped", index=False, escape=False)
    return render_template_string(HTML_TEMPLATE, df_html=html, path=path)

@app.route("/download")
def download():
    path = os.path.join(os.getcwd(), "info.csv")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "info.csv not found", 404

if __name__ == "__main__":
    # Ejecutar: python web_table.py
    app.run(host="127.0.0.1", port=5000, debug=False)