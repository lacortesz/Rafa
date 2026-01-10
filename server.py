import asyncio
import websockets
import json
import os
import utils.utils as utils
from datetime import datetime
import parameters

clients = set()
message_queue = asyncio.Queue(maxsize=10000)

# Carpeta para guardar CSVs (puedes mantener la ruta absoluta si prefieres)
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
                utils.save_bars_csv,
                payload,
                OUT_DIR,
                True
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


async def main():
    server = await websockets.serve(
        handler,
        "127.0.0.1",
        8765,
        max_size=None
    )

    print("Servidor WebSocket activo ws://127.0.0.1:8765")

    # 🔥 workers paralelos (ajusta según CPU)
    workers = [asyncio.create_task(worker(i)) for i in range(6)]

    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())