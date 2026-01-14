from confluent_kafka import Producer, Consumer, KafkaException
from utility.utility import init_kafka_producer, send_result as send_result_blocking
import utility.utility as utility
import json

## Kafka configuration (can be overridden via environment variables)
#KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:8003")
#KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_DATA_GATEWAY", "data_gateway")
KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "data_gateway"
#configuración del productor de Kafka
producer_conf = {"bootstrap.servers": KAFKA_BOOTSTRAP}
producer = Producer(producer_conf)

#configuración del consumidor de Kafka
consumer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "group.id": "data-gateway-group",
    "auto.offset.reset": "earliest"
}
consumer = Consumer(consumer_conf)
consumer.subscribe([KAFKA_TOPIC])

print("🟢 Consumer iniciado. Esperando mensajes...")

try:
    while True:
        msg = consumer.poll(1.0)  # Espera 1 segundo por un mensaje

        if msg is None:
            continue
        if msg.error():
            print(f"Error del consumidor: {msg.error()}")
            continue

        # Procesa el mensaje recibido
        topic = msg.topic()
        payload = json.loads(msg.value().decode("utf-8"))
        print(f"Mensaje recibido en {topic}: {payload}")

        # Aquí podrías agregar lógica adicional para procesar el mensaje    
        utility.process_file(payload)

except KeyboardInterrupt:
    print("Interrupción por teclado recibida. Saliendo...")
finally:
    consumer.close()

init_kafka_producer(KAFKA_BOOTSTRAP)
