import json
from confluent_kafka import Consumer, Producer

# Configuración de Kafka
KAFKA_BOOTSTRAP = "localhost:9092"

# Configuración del consumidor y productor de Kafka
consumer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "group.id": "rafa-orchestrator",
    "auto.offset.reset": "earliest"
}

producer_conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP
}

# Inicializa el consumidor y productor de Kafka
consumer = Consumer(consumer_conf)
producer = Producer(producer_conf)

# Suscribe el consumidor a los topics relevantes
consumer.subscribe(["data_gateway", "process_data"])

def publish_message(topic, message):
    """
    Publica un mensaje en un topic de Kafka.
    parametros:
        topic: str, nombre del topic
        message: dict, mensaje a publicar
    """
    producer.produce(topic, json.dumps(message).encode("utf-8"))
    producer.flush()
    print(f"Mensaje publicado en {topic}: {message}")

print("Orquestador Kafka inicializado y suscrito a topics.")

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

    # Lógica de orquestación basada en el topic y payload
    if topic == "data_gateway":
        # confirma archivo  el resultado al microservicio process_data
        publish_message("process_data", payload)
    elif topic == "process_data":
        # Aquí podrías agregar lógica adicional para manejar respuestas de process_data
        print(f"Procesamiento completado: {payload}")