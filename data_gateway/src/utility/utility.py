import os
import threading
import pandas as pd

_FILE_SAVE_LOCK = threading.Lock()

def save_bars_csv(payload, out_dir=None):
    """
    Guarda payload {'symbol', 'timeframe', 'bars'} en CSV:
      - out_dir/{symbol}_{timeframe}.csv
    parametros:
        payload: dict con 'symbol', 'timeframe', 'bars' (lista de OHLC)
        out_dir: carpeta para guardar CSVs
    retorna:
      {symbol, timeframe, received_rows, stored_rows, file}
    """
    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), "received_data")
    os.makedirs(out_dir, exist_ok=True)

    symbol = payload.get("symbol") or payload.get("ticker") or payload.get("instrument") or "UNKNOWN"
    timeframe = payload.get("timeframe") or payload.get("interval") or "UNKNOWN"
    bars = payload.get("bars") or payload.get("data") or payload.get("ohlc")
    if not bars:
        raise ValueError("No 'bars' array found in payload")

    df = bars_to_df(bars)
    df["symbol"] = symbol
    df["timeframe"] = timeframe

    filename = f"{symbol}_{timeframe}.csv"
    out_path = os.path.join(out_dir, filename)

    with _FILE_SAVE_LOCK:
        """if os.path.exists(out_path):
            try:
                df_existing = pd.read_csv(out_path, parse_dates=["datetime"], dayfirst=False)
            except Exception:
                df_existing = pd.read_csv(out_path)
            df_combined = pd.concat([df_existing, df], ignore_index=True, sort=False)
            if "datetime" in df_combined.columns:
                df_combined = df_combined.drop_duplicates(subset=["datetime"], keep="last")
                df_combined = df_combined.sort_values(by="datetime").reset_index(drop=True)
            else:
                df_combined = df_combined.drop_duplicates().reset_index(drop=True)
            df_combined.to_csv(out_path, index=False)
            stored_rows = len(df_combined)
        else:"""
        df.to_csv(out_path, index=False)
        stored_rows = len(df)

    return {"symbol": symbol, "timeframe": timeframe, "received_rows": len(df), "stored_rows": stored_rows, "file": out_path}

def bars_to_df(bars):
    """Normaliza 'bars' (lista de dicts o dict de listas) a DataFrame con columna 'datetime'."""
    if isinstance(bars, dict):
        df = pd.DataFrame(bars)
    else:
        df = pd.DataFrame(bars)

    datetime_cols = [c for c in df.columns if c.lower() in ("datetime", "time", "timestamp", "date")]
    if datetime_cols:
        dt_col = datetime_cols[0]
        df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
        if dt_col != "datetime":
            df = df.rename(columns={dt_col: "datetime"})
    else:
        df["datetime"] = pd.NaT

    return df

# --- Kafka helpers moved here from main.py ---
import json
try:
    from confluent_kafka import Producer
except Exception:
    Producer = None

# Module-level producer (initialized by init_kafka_producer)
producer = None


def init_kafka_producer(bootstrap_servers=None):
    """Initialize and store a confluent_kafka Producer in this module.

    bootstrap_servers: str, e.g. 'localhost:9092'. If None, read from env KAFKA_BOOTSTRAP.
    Returns the producer instance or None on failure.
    """
    global producer
    if Producer is None:
        print("confluent_kafka.Producer not available in environment")
        producer = None
        return None

    bs = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP", "localhost:8003")
    try:
        conf = {"bootstrap.servers": bs}
        producer = Producer(conf)
        print(f"Kafka producer initialized (bootstrap={bs})")
        return producer
    except Exception as e:
        producer = None
        print("Failed to initialize Kafka producer:", e)
        return None


def publish_to_kafka(message, topic, timeout=5):
    """Blocking publish of `message` (dict) to `topic` using the module-level producer.

    Raises any exceptions from confluent_kafka to the caller.
    """
    if producer is None:
        raise RuntimeError("Kafka producer not initialized")

    def delivery_report(err, msg):
        if err is not None:
            print("Kafka delivery failed:", err)
        else:
            try:
                print(f"Kafka message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
            except Exception:
                print("Kafka message delivered (meta unavailable)")

    producer.produce(topic, json.dumps(message).encode("utf-8"), callback=delivery_report)
    producer.flush(timeout=timeout)


def send_result(result, topic=None):
    """Convenience wrapper to publish result to Kafka topic (sync/blocking).

    Designed to be called from `run_in_executor` or directly in blocking contexts.
    """
    t = topic or os.getenv("KAFKA_TOPIC_DATA_GATEWAY", "data_gateway")
    publish_to_kafka(result, t)
