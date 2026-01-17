# config.py
from pathlib import Path

DATABASE_URL = "postgresql+psycopg2://admin:admin123@localhost:5432/trading_db"

DATA_DIR = Path(r"C:/repo_luis/Rafa/received_data")

KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_GROUP_ID = "process-data-group-id"
KAFKA_TOPIC = "process_data"
