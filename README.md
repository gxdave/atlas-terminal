# Atlas Terminal v1.1.1

Candlestick Pattern Probability Analyzer mit FastAPI Backend und HTML Frontend

## 🚀 Installation

1. **Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```

## 💻 Verwendung

### Backend starten:

```bash
python backend.py
```

Das Backend läuft dann auf: `http://127.0.0.1:8000`

### Frontend öffnen:

Öffne die Datei `frontend.html` einfach in deinem Browser.

## 📋 Features

- **Asset Auswahl**: FX-Paare, Commodities, Indizes, Aktien
- **Pattern Builder**: Dynamische Candlestick-Pattern erstellen
- **Probability Analysis**: Berechnung der Wahrscheinlichkeiten für die nächste Kerze
- **Live Data**: Daten von Yahoo Finance (yfinance)
- **Visuelle Darstellung**: Übersichtliche Ergebnisse mit Diagrammen

## 🛠️ Technologie Stack

- **Backend**: FastAPI + Uvicorn
- **Frontend**: HTML + Vanilla JavaScript
- **Datenquelle**: yfinance
- **Analyse**: pandas, numpy

## 📊 API Endpoints

- `GET /` - API Status
- `GET /api/assets` - Verfügbare Assets
- `GET /api/timeframes` - Verfügbare Timeframes
- `POST /api/analyze` - Pattern Analyse durchführen
- `GET /api/market-data/{symbol}` - Marktdaten für ein Symbol
- `GET /health` - Health Check

## 🔧 Konfiguration

Die Asset-Liste kann in `backend.py` angepasst werden:

```python
ASSETS = {
    "FX-Paare": {...},
    "Commodities": {...},
    ...
}
```

## 📝 Beispiel Request

```json
{
  "pattern": ["Bullish", "Bearish"],
  "symbol": "EURUSD=X",
  "timeframe": "1d",
  "period": "5y"
}
```

## ⚠️ Hinweise

- Das Backend muss laufen, bevor das Frontend verwendet wird
- CORS ist für lokale Entwicklung konfiguriert (`allow_origins=["*"]`)
- Für Production sollte CORS eingeschränkt werden

## 🐛 Troubleshooting

**Problem**: Frontend kann Backend nicht erreichen
- Stelle sicher, dass das Backend läuft (`python backend.py`)
- Überprüfe die URL in `frontend.html` (Zeile: `const API_URL = 'http://127.0.0.1:8000'`)

**Problem**: Keine Daten für Symbol verfügbar
- Überprüfe den Symbol-Namen (z.B. "EURUSD=X" für Forex)
- Versuche ein anderes Symbol

## 📧 Support

Bei Fragen oder Problemen siehe die Logs im Backend Terminal.
