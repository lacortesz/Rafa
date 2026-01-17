import pandas as pd
from urllib.parse import quote_plus

# Build HTML
def build_trend_table_html(df: pd.DataFrame) -> str:
        """
        Build HTML table for trend data with links to charts.
        parameter:
            final_df: DataFrame with trend data
        return: HTML string
        """
        html = ['<table>']
        html.append('<thead><tr><th>Symbol</th>')
        for c in df.columns:
            html.append(f'<th>{c}</th>')
        html.append('</tr></thead>')
        html.append('<tbody>')
        for sym in df.index:
            html.append(f'<tr><td>{sym}</td>')
            for c in df.columns:
                if c == 'rsi':
                    cell_val = df.loc[sym, c]
                    display_html = f"{cell_val:.2f}" if not pd.isna(cell_val) and cell_val != '' else ''
                    html.append(f'<td>{display_html}</td>')
                else:
                    cell_val = df.loc[sym, c]
                    display_html = colorize_trend(cell_val)
                    # Agregar enlace a la gráfica
                    sym_q = quote_plus(str(sym))
                    tf_q = quote_plus(str(c))
                    link = f'/chart?symbol={sym_q}&timeframe={tf_q}'
                    cell_html = f'<a class="cell-link" href="{link}" target="_blank">{display_html or "–"}</a>'
                    html.append(f'<td>{cell_html}</td>')
            html.append('</tr>')
        html.append('</tbody></table>')
        table_html = "\n".join(html)

        return table_html

def colorize_trend(val):
    """
        according to the trend colorized the text
        parameter:
            val
        return html string according to treng
    """
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