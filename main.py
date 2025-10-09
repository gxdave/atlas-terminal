from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Erlaubt Anfragen von lokalem HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # für Testzwecke ok
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/analyze")
def analyze(symbol: str = "EURUSD"):
    # Dummy-Auswertung
    return {
        "symbol": symbol,
        "probability": "63%",
        "direction": "bullish"
    }