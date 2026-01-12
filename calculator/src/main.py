from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from math import floor
from pathlib import Path
import json

app = FastAPI()

# ---------- CORS ----------
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/specs",
    StaticFiles(directory=Path(__file__).resolve().parent / "specs"),
    name="specs"
)
print(f"Serving specs at /specs (dir: {Path(__file__).resolve().parent / 'specs'})")

#----- Load contract specs from JSON file next to this module
_SPECS_FILE = Path(__file__).resolve().parent / "specs/cme_contract_specs.json"

def load_contract_specs(file_path: Path = _SPECS_FILE):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Invalid contract specs file format (expected dict at top level)")
        return data
    except Exception as e:
        print(f"⚠️ Could not load contract specs from {file_path}: {e}")
        return {}

CONTRACT_SPECS = load_contract_specs()

# ---------- REQUEST ----------
class LoteRequest(BaseModel):
    symbol: str
    account_size: float
    risk_percent: float
    entry_price: float
    stop_price: float

# ---------- ENDPOINT ----------
@app.post("/calcular-lotes")
def calcular_lotes(req: LoteRequest):

    specs = CONTRACT_SPECS.get(req.symbol.strip())
    if specs is None:
        raise HTTPException(status_code=400, detail=f"Unknown symbol: {req.symbol}")

    riesgo_dolares = req.account_size * (req.risk_percent / 100)
    ticks = abs(req.entry_price - req.stop_price) / specs["tick_size"]
    riesgo_por_contrato = ticks * specs["tick_value"]

    contrato_decimales = riesgo_dolares / riesgo_por_contrato
    contratos = floor(riesgo_dolares / riesgo_por_contrato)

    return {
        "symbol": req.symbol,
        "riesgo_dolares": round(riesgo_dolares, 2),
        "ticks": ticks,
        "riesgo_por_contrato": riesgo_por_contrato,
        "contrato_decimales": contrato_decimales,
        "contratos": contratos
    }
