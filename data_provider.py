import time
import signal
import threading
import logging

# data_provider.py
# Ejecuta la función `provide_data` cada 15 minutos (900 segundos).
# Ctrl+C o señal TERM para terminar limpiamente.


# Intervalo en segundos (15 minutos)
INTERVAL = 3 * 60

stop_event = threading.Event()

def _handle_signal(signum, frame):
    logging.info("Señal recibida, deteniendo...")
    stop_event.set()

signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)

def provide_data():
    """
    Coloque aquí la lógica que debe ejecutarse cada 15 minutos.
    Ejemplo: consultar una API, generar/guardar datos, subir a un servicio, etc.
    """
    logging.info("Inicio de provide_data")
    # TODO: reemplazar con la lógica real
    # Ejemplo de tarea simulada:
    time.sleep(1)
    logging.info("Tarea completada")

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Iniciando data_provider (intervalo: %s segundos)", INTERVAL)

    # Ejecutar inmediatamente al inicio
    while not stop_event.is_set():
        start = time.time()
        try:
            provide_data()
        except Exception:
            logging.exception("Error en provide_data")
        elapsed = time.time() - start
        # Esperar el tiempo restante hasta completar INTERVAL, respetando la señal de parada
        wait_time = max(0, INTERVAL - elapsed)
        logging.info("Esperando %s segundos hasta la siguiente ejecución", round(wait_time, 1))
        stop_event.wait(wait_time)

    logging.info("Data provider detenido")

if __name__ == "__main__":
    main()