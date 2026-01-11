import asyncio
import websockets
import json
import os
import src.utility.parameters as parameters
import src.utility.utility as utility 
import requests

# Inicializa variables globales
## Variables websockets
clients = set()
message_queue = asyncio.Queue(maxsize=10000)

## Variables fastapi
url = "http://localhost:8000/data_gateway"

# Carpeta para guardar CSVs !!Revisar para configurar un file server
OUT_DIR = parameters.OUT_DIR
os.makedirs(OUT_DIR, exist_ok=True)

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
            await send_result({"Result": "Data saved", "details": summary})

        except Exception as e:
            print(f"[Worker {worker_id}] Error:", e)
            await send_result({"Result": "Error", "details": str(e)})

        finally:
            message_queue.task_done()
            
async def send_result(result):
    response = requests.post(url, json=result, timeout=10)
    print("Status:", response.status_code)
    print("Response:", response.json())


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


