import uvicorn
import subprocess, sys, atexit
from pathlib import Path

def start_static_server(port=8010):
    src_dir = Path(__file__).resolve().parent / "src"
    p = subprocess.Popen([sys.executable, "-m", "http.server", str(port)], cwd=str(src_dir))
    atexit.register(lambda: p.terminate())

if __name__ == "__main__":
    start_static_server(8010)
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)