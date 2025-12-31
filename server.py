import asyncio
import websockets
import json
import os
import utils
from datetime import datetime
import parameters

clients = set()

# Carpeta para guardar CSVs (puedes mantener la ruta absoluta si prefieres)
OUT_DIR = parameters.OUT_DIR
os.makedirs(OUT_DIR, exist_ok=True)

async def handler(websocket, path=None):
    if path is None:
        path = getattr(websocket, "path", None)

    print(f"Cliente conectado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {websocket.remote_address}, path: {path}")
    clients.add(websocket)

    try:
        async for msg in websocket:
            try:
                payload = json.loads(msg)
            except Exception as e:
                resp = {"status": "error", "reason": "invalid_json", "message": str(e)}
                await websocket.send(json.dumps(resp))
                continue

            try:
                summary = utils.save_bars_csv(payload, out_dir=OUT_DIR, add_indicators=True)
                resp = {"status": "ok", "summary": summary}
                print(f"Guardado: {summary['file']} (stored_rows={summary['stored_rows']})")
                await websocket.send(json.dumps(resp))
            except Exception as e:
                print("Error guardando datos:", e)
                resp = {"status": "error", "reason": "save_failed", "message": str(e)}
                await websocket.send(json.dumps(resp))

    except websockets.ConnectionClosed:
        print("Cliente desconectado")
    finally:
        clients.discard(websocket)

async def main():
    server = await websockets.serve(
        handler,
        "127.0.0.1",
        8765,
        max_size=None
    )
    print("Servidor WebSocket activo en ws://127.0.0.1:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())