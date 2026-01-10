"""trends.py

Scan CSV files in `received_data/`, compute a simple trend per instrument/timeframe
and return a summary `DataFrame` that can be queried.

Trend method: percent change over last `window` bars. If pct >= up_threshold -> 'up'
if pct <= down_threshold -> 'down' otherwise 'sideways'.

Usage:
    from trends import compute_trends, get_trend
    df = compute_trends('received_data', window=20, up_threshold=0.01, down_threshold=-0.01)
    row = get_trend(df, '6A', '15m')
"""
from __future__ import annotations

import os
import re
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import utils


TF_NORMALIZATION = {
    '1d': '1d', 'daily': '1d', 'daily.csv': '1d',
    '60m': '60m', '60 minute': '60m', '60m.csv': '60m',
    '240m': '240m', '240 minute': '240m', '240m.csv': '240m',
    '15m': '15m', '15 minute': '15m', '15m.csv': '15m',
    '5m': '5m', '5 minute': '5m', '5m.csv': '5m'
}


def _normalize_timeframe(token: str) -> Optional[str]:
    if token is None:
        return None
    t = token.strip().lower()
    # direct match
    if t in TF_NORMALIZATION:
        return TF_NORMALIZATION[t]
    # token like '1d', '60m', '240m', '15m'
    m = re.match(r"^(\d+)(m|d)$", t)
    if m:
        num, unit = m.groups()
        if unit == 'd':
            return '1d'
        return f"{num}m"
    # token like 'unknown', fallback
    return None


def _parse_filename(filepath: str) -> Tuple[str, str]:
    """Return (instrument, timeframe) extracted from filename.

    Heuristics:
    - Split filename by underscores/spaces, instrument is first token.
    - Timeframe is guessed from last token and normalized.
    - If not found, will try to find any token that maps to a known timeframe.
    """
    base = os.path.basename(filepath)
    name, _ = os.path.splitext(base)
    tokens = re.split(r"[_\s]+", name)
    instrument = tokens[0]

    # Try last token first
    tf = _normalize_timeframe(tokens[-1] if tokens else '')
    if tf:
        return instrument, tf

    # Scan tokens for any recognizable timeframe
    for tok in reversed(tokens):
        tf = _normalize_timeframe(tok)
        if tf:
            return instrument, tf

    # as last resort, look for explicit patterns in the filename
    m = re.search(r"(\d+d|\d+m)", name.lower())
    if m:
        tf = _normalize_timeframe(m.group(1))
        if tf:
            return instrument, tf

    # fallback
    return instrument, 'unknown'


def _read_csv_guess_datetime(filepath: str) -> pd.DataFrame:
    """Read CSV and try to identify datetime column. Returns DataFrame with a DatetimeIndex.

    Expected CSVs in `received_data` have typical OHLC columns; function is defensive.
    """
    df = pd.read_csv(filepath)
    # find a datetime-like column
    datetime_cols = [c for c in df.columns if re.search(r'date|time|timestamp', c, re.I)]
    if datetime_cols:
        dtc = datetime_cols[0]
        df[dtc] = pd.to_datetime(df[dtc], errors='coerce')
        df = df.dropna(subset=[dtc])
        df = df.set_index(dtc)
        df.index.name = 'datetime'
        return df.sort_index()

    # try first column
    first_col = df.columns[0]
    try:
        df[first_col] = pd.to_datetime(df[first_col], errors='coerce')
        df = df.dropna(subset=[first_col])
        df = df.set_index(first_col)
        df.index.name = 'datetime'
        return df.sort_index()
    except Exception:
        # fallback: return as-is
        return df


def _compute_trend_from_prices(prices: pd.Series, window: int, up_threshold: float, down_threshold: float) -> Tuple[str, float]:
    """Compute percent change over the last `window` bars and classify trend."""
    if prices is None or len(prices) == 0:
        return 'unknown', 0.0
    n = min(len(prices), window)
    slice_ = prices.iloc[-n:]
    first, last = slice_.iloc[0], slice_.iloc[-1]
    if first == 0:
        pct = 0.0
    else:
        pct = (last - first) / float(first)

    if pct >= up_threshold:
        return 'up', pct
    if pct <= down_threshold:
        return 'down', pct
    return 'sideways', pct


def compute_trends(received_dir: str = 'received_data', window: int = 20, up_threshold: float = 0.01, down_threshold: float = -0.01) -> pd.DataFrame:
    """Scan CSV files inside `received_dir` and compute a trend summary DataFrame.

    Returns a DataFrame with columns:
        instrument, timeframe, last_ts, trend, pct_change, last_price, n_bars, file

    Example:
        df = compute_trends('received_data', window=30)
        get_trend(df, '6A', '15m')
    """
    rows = []
    if not os.path.isdir(received_dir):
        raise ValueError(f"Directory not found: {received_dir}")

    csv_files = [os.path.join(received_dir, f) for f in os.listdir(received_dir) if f.lower().endswith('.csv')]
    for fpath in csv_files:
        try:
            instrument, tf = _parse_filename(fpath)
            df = _read_csv_guess_datetime(fpath)
            # prefer 'close' column if present, else last numeric column
            price = None
            if 'close' in (c.lower() for c in df.columns):
                # keep original case
                closecol = [c for c in df.columns if c.lower() == 'close'][0]
                price = df[closecol].astype(float)
            else:
                # pick last numeric column
                numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                if numeric_cols:
                    price = df[numeric_cols[-1]].astype(float)

            trend, pct = _compute_trend_from_prices(price, window, up_threshold, down_threshold)
            last_ts = None
            last_price = None
            n_bars = 0
            if price is not None and len(price) > 0:
                last_ts = price.index[-1]
                last_price = float(price.iloc[-1])
                n_bars = len(price)

            rows.append({
                'instrument': instrument,
                'timeframe': tf,
                'last_ts': last_ts,
                'trend': trend,
                'pct_change': pct,
                'last_price': last_price,
                'n_bars': n_bars,
                'file': os.path.basename(fpath),
            })
        except Exception as exc:
            # in production we might log; for now, append an error row
            rows.append({
                'instrument': None,
                'timeframe': None,
                'last_ts': None,
                'trend': 'error',
                'pct_change': 0.0,
                'last_price': None,
                'n_bars': 0,
                'file': os.path.basename(fpath),
                'error': str(exc)
            })

    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary = summary.sort_values(['instrument', 'timeframe']).reset_index(drop=True)
    return summary


def compute_summary(received_dir: str = 'received_data', pivot_n: int = 2, sr_window: int = 10, sr_tolerance: float = 0.005, sr_top_n: int = 2, trend_n: int = 3, rsi_period: int = 14) -> pd.DataFrame:
    """Scan CSV files and compute pivots, supports/resistances, trend and RSI.

    Returns a DataFrame indexed by (instrument, timeframe) with columns:
      last_ts, trend, rsi, soportes, resistencias, n_bars, file, error
    """
    rows = []
    if not os.path.isdir(received_dir):
        raise ValueError(f"Directory not found: {received_dir}")

    csv_files = [os.path.join(received_dir, f) for f in os.listdir(received_dir) if f.lower().endswith('.csv')]
    for fpath in csv_files:
        try:
            instrument, tf = _parse_filename(fpath)
            df = _read_csv_guess_datetime(fpath)

            # run pivots
            pivots_df = None
            soportes = []
            resistencias = []
            trend = None
            rsi_last = None

            try:
                pivots_df = utils.identificar_pivots(df, n=pivot_n)
            except Exception as e:
                # continue; pivots may fail on malformed data
                pivots_df = None
                pivots_err = str(e)
            else:
                pivots_err = None

            try:
                soportes, resistencias = utils.identificar_soportes_resistencias(df, window=sr_window, tolerance=sr_tolerance, top_n=sr_top_n)
            except Exception as e:
                soportes, resistencias = [], []

            try:
                if pivots_df is not None:
                    trend = utils.determinar_tendencia(pivots_df, n=trend_n)
                else:
                    trend = 'unknown'
            except Exception:
                trend = 'error'

            try:
                if 'Close' in df.columns:
                    rsi_series = utils.calcular_rsi(df['Close'], period=rsi_period)
                    if rsi_series is not None and not rsi_series.dropna().empty:
                        rsi_last = float(rsi_series.dropna().iloc[-1])
                else:
                    rsi_last = None
            except Exception:
                rsi_last = None

            last_ts = df.index[-1] if len(df) > 0 else None
            n_bars = len(df)

            rows.append({
                'instrument': instrument,
                'timeframe': tf,
                'last_ts': last_ts,
                'trend': trend,
                'rsi': rsi_last,
                'soportes': soportes,
                'resistencias': resistencias,
                'n_bars': n_bars,
                'file': os.path.basename(fpath),
                'error': pivots_err
            })
        except Exception as exc:
            rows.append({
                'instrument': None,
                'timeframe': None,
                'last_ts': None,
                'trend': 'error',
                'rsi': None,
                'soportes': [],
                'resistencias': [],
                'n_bars': 0,
                'file': os.path.basename(fpath),
                'error': str(exc)
            })

    df_summary = pd.DataFrame(rows)
    if df_summary.empty:
        return df_summary

    df_summary = df_summary.set_index(['instrument', 'timeframe'])
    return df_summary


def get_summary(summary_df: pd.DataFrame, instrument: str, timeframe: str) -> Optional[pd.Series]:
    """Return row for given instrument & timeframe from a compute_summary result."""
    if summary_df is None or summary_df.empty:
        return None
    try:
        return summary_df.loc[(str(instrument), str(timeframe))]
    except Exception:
        # try case-insensitive search
        mask = (
            (summary_df.index.get_level_values('instrument').astype(str).str.upper() == str(instrument).upper()) &
            (summary_df.index.get_level_values('timeframe').astype(str).str.lower() == str(timeframe).lower())
        )
        res = summary_df[mask]
        if res.empty:
            return None
        return res.iloc[0]


def save_trends_csv(summary_df: pd.DataFrame, out_dir: str = 'data', filename: str = 'trends.csv', name_sep: str = '_') -> str:
    """Save trends to CSV with columns 'name' and 'trend'. Name is 'instrument{sep}timeframe'.

    Returns the path to the written file.
    """
    if summary_df is None or summary_df.empty:
        raise ValueError("summary_df is empty")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    df = summary_df.reset_index()
    if not set(['instrument', 'timeframe', 'trend']).issubset(df.columns):
        raise ValueError("summary_df must contain 'instrument', 'timeframe' and 'trend' columns")

    df['name'] = df['instrument'].astype(str) + name_sep + df['timeframe'].astype(str)
    out_df = df[['name', 'trend']]
    out_df.to_csv(out_path, index=False)
    return out_path


def get_trend(summary_df: pd.DataFrame, instrument: str, timeframe: str) -> Optional[pd.Series]:
    """Query a previously computed summary DataFrame for an instrument & timeframe."""
    return get_summary(summary_df, instrument, timeframe)


if __name__ == '__main__':
    # quick demo when executed directly
    s = compute_trends('received_data', window=20, up_threshold=0.01, down_threshold=-0.01)
    print('Trends summary:')
    print(s.to_string(index=False))

    print('\nDetailed summary using utils functions:')
    summary = compute_summary('received_data')
    print(summary.head())

    # Save to data/trends.csv
    try:
        path = save_trends_csv(summary, out_dir='data', filename='trends.csv')
        print(f"Saved trends CSV to {path}")
    except Exception as e:
        print(f"Error saving trends CSV: {e}")
