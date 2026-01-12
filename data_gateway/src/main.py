import asyncio
import websockets
import json
from confluent_kafka import Producer
import os
import src.utility.parameters as parameters
import src.utility.utility as utility 
from src.utility.utility import init_kafka_producer, send_result as send_result_blocking

#--- VARIABLES GLOBALES
## Variables websockets
clients = set()
message_queue = asyncio.Queue(maxsize=10000)

## Carpeta para guardar CSVs !!Revisar para configurar un file server
OUT_DIR = parameters.OUT_DIR
os.makedirs(OUT_DIR, exist_ok=True)

## Kafka configuration (can be overridden via environment variables)
#KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:8003")
#KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_DATA_GATEWAY", "data_gateway")
KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "data_gateway"
producer_conf = {"bootstrap.servers": KAFKA_BOOTSTRAP}
producer = Producer(producer_conf)

if producer is None:
    print("Failed to initialize Kafka producer. Exiting.")
    exit(1)
else:
    print(f"Kafka producer initialized (bootstrap={KAFKA_BOOTSTRAP}) {producer}")

#--- FUNCIONES
## WEBSOCKET FUNCTIONS
### websocket handler
async def handler(websocket, path=None):
    print(f"Cliente conectado {websocket.remote_address}")
    clients.add(websocket)

    try:
        async for msg in websocket:
            try:
                payload = json.loads(msg)
            except json.JSONDecodeError:
                continue

            await message_queue.put(payload)

    except websockets.ConnectionClosed:
        print("Cliente desconectado")
    finally:
        clients.discard(websocket)

## websocket worker function
async def worker(worker_id: int):
    loop = asyncio.get_running_loop()

    while True:
        payload = await message_queue.get()

        try:
            # Ejecuta la función pesada fuera del event loop
            summary = await loop.run_in_executor(
                None,
                utility.save_bars_csv,
                payload,
                OUT_DIR
            )

            print(
                f"[Worker {worker_id}] "
                f"{summary['symbol']} {summary['timeframe']} "
                f"rows={summary['stored_rows']}"
            )
        except Exception as e:
            print(f"[Worker {worker_id}] Error:", e)
        finally:
            message_queue.task_done()

        try:
            await send_result({"Result": "Data saved", "details": summary})
            print(f"[Worker {worker_id}] Sending result to Kafka: OK")

        except Exception as e:
            print(f"[Worker {worker_id}] Error sending result to Kafka:", e)

## KAFKA FUNCTIONS
### reporte de entrega mensaje
def delivery_report(err, msg):
    if err is not None:
        print("Kafka delivery failed:", err)
    else:
        print(
            f"✅ Message delivered to {msg.topic()} "
            f"[partition {msg.partition()}] "
            f"at offset {msg.offset()}"
        )

### enviar resultado a kafka (async)
async def send_result(result, topic=KAFKA_TOPIC):
    """Envía resultado a Kafka de forma asíncrona usando run_in_executor."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        send_result_blocking,
        result,
        topic
    )

async def main():
    server = await websockets.serve(
        handler,
        "127.0.0.1",
        8765,
        max_size=None
    )

    print("Servidor WebSocket activo ws://127.0.0.1:8001")

    # 🔥 workers paralelos (ajusta según CPU)
    workers = [asyncio.create_task(worker(i)) for i in range(6)]

    await server.wait_closed()


