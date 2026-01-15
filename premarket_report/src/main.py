import utility.utility as utils
import json

# 1. read orchestor. topic process_data
consumer = utils.init_kafka_consumer("localhost:9092", "process-data-group-id", "process_data")  

if consumer != None:
    print("🟢 Consumer iniciado. Esperando mensajes...")
else:
    print("Error al inicializar kafka consumer")

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

        # procesa e archivo. identifica tendencia, soportes y resistencia y almacena archivo csv actualizado y resumen en db
        utility.process_file(payload)

        # Confirmar actualziacion al orchestator
        message = utility.message_json(payload)
        utility.send_result(message, "process_data")


except KeyboardInterrupt:
    print("Interrupción por teclado recibida. Saliendo...")
finally:
    consumer.close()

# 2. read database trading_db en el symbol - timeframe actualizado

# 3. update grid in web page con el nuevo valor

# 4. Graph if click on a field