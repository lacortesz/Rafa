# config.py
import os
from pathlib import Path

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://admin:admin123@localhost:5432/trading_db"
)

# Data directory
DATA_DIR = Path(os.getenv("DATA_DIR", r"C:\repo_luis\Rafa\received_data"))

# Kafka configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "process-data-group-id")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "process_data")
