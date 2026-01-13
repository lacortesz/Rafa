
import os
import json

try:
    from confluent_kafka import Producer    
except Exception:
    Producer = None

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
