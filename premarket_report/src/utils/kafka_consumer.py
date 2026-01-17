# services/kafka_consumer.py
import json
import threading
from flask_socketio import SocketIO
from config import KAFKA_BOOTSTRAP, KAFKA_GROUP_ID, KAFKA_TOPIC
from confluent_kafka import Consumer

def start_consumer(socketio: SocketIO) -> None:
    """
    Starts Kafka consumer in a daemon thread.
    """

    def _consume():
        consumer = init_kafka_consumer(
            KAFKA_BOOTSTRAP,
            KAFKA_GROUP_ID,
            KAFKA_TOPIC
        )

        if not consumer:
            print("Kafka consumer initialization failed")
            return

        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            payload = json.loads(msg.value().decode())
            print("Kafka message:", payload)
            socketio.emit("refresh")

    threading.Thread(target=_consume, daemon=True).start()

def init_kafka_consumer(bootstrap_server, group_id, topics):
    """
    Create kafka consumer
    parameters:
        bootstrap_server
        group_id
        topics
    return:
        consumer object
    """

    consumer_conf = {
      "bootstrap.servers": bootstrap_server,
        "group.id": group_id,
        "auto.offset.reset": "earliest"  
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe(["process_data"])

    return consumer