# Risk Radar - Atlas Terminal Integration

## Überblick

Der **Risk Radar** ist ein Market Stress Monitor, der Markt-Stressindikatoren analysiert und visualisiert. Er wurde aus deinen Jupyter Notebooks extrahiert und in das Atlas Terminal integriert.

## Features

### 1. **Echtzeit Markt-Stress Monitoring**
- Composite Z-Score Berechnung aus 4 Hauptindikatoren
- Regime-Klassifikation: CALM, WATCH, WARNING, ALERT
- Automatische Schwellenwert-Überwachung

### 2. **Indikatoren**
- **HY_OAS**: High Yield Option-Adjusted Spread (30% Gewichtung)
- **IG_OAS**: Investment Grade Corporate OAS (20% Gewichtung)
- **STLFSI**: St. Louis Fed Financial Stress Index (25% Gewichtung)
- **VIX**: Volatility Index (25% Gewichtung)

### 3. **Visualisierungen**
- Interaktiver Chart mit historischen Composite Z-Scores (6 Monate)
- Schwellenwert-Linien (WATCH, WARNING, ALERT)
- Regime-Hintergrund-Färbung
- Einzelkomponenten-Anzeige

### 4. **Alerts & Statistiken**
- Letzte Regime-Wechsel und Alerts
- Regime-Verteilung (letzte 12 Monate)
- Composite Z-Score Statistiken (Mean, Std Dev, Max, Min)

## Technische Details

### Backend API Endpoint
```
GET /api/risk-radar
```

**Response Structure:**
```json
{
  "status": "success",
  "timestamp": "2025-10-12T...",
  "current_state": {
    "date": "2025-10-12",
    "composite_z": 0.45,
    "regime": "CALM",
    "components": {
      "HY_OAS": {"value": 0.32, "date": "2025-10-12"},
      "IG_OAS": {"value": 0.21, "date": "2025-10-12"},
      "STLFSI": {"value": 0.15, "date": "2025-10-12"},
      "VIX": {"value": 0.67, "date": "2025-10-12"}
    }
  },
  "alerts": [...],
  "historical_data": [...],
  "statistics": {...},
  "thresholds": {...}
}
```

### Regime Schwellenwerte
- **CALM**: Composite Z-Score < 1.0
- **WATCH**: Composite Z-Score >= 1.0
- **WARNING**: Composite Z-Score >= 1.75
- **ALERT**: Composite Z-Score >= 2.5

Zusätzlich werden einzelne Indikatoren-Flags berücksichtigt:
- STLFSI: Schwellenwert 1.0
- HY_OAS, IG_OAS, VIX: Schwellenwert 1.5

### Z-Score Berechnung
```python
lookback = 252  # 1 Jahr Handelstage
rolling_mean = data.rolling(window=252, min_periods=int(252*0.8)).mean()
rolling_std = data.rolling(window=252, min_periods=int(252*0.8)).std()
z_score = (data - rolling_mean) / rolling_std
z_score = z_score.clip(-3, 3)  # Outlier beschneiden
```

## Installation & Setup

### 1. Dependencies
```bash
pip install fredapi
```

Bereits in `requirements.txt` enthalten:
```
fredapi==0.5.2
```

### 2. FRED API Key
Der Risk Radar benötigt einen FRED API Key für Datenabfrage.

**Kostenloser API Key:**
1. Registrierung auf: https://fred.stlouisfed.org/
2. API Key erstellen unter: https://fred.stlouisfed.org/docs/api/api_key.html

**Setup:**
- Entweder als Environment Variable: `FRED_API_KEY=your_key_here`
- Oder im Code: Standard-Key ist bereits hinterlegt (funktioniert für Tests)

### 3. Backend starten
```bash
cd "Atlas Terminal/V1.1.1"
python backend.py
```

Oder mit Uvicorn:
```bash
uvicorn backend:app --reload --port 8000
```

### 4. Frontend öffnen
```
http://localhost:8000/terminal.html
```

Navigiere zu **Risk Radar** im Sidebar-Menü.

## Verwendung

1. **Terminal öffnen**: Navigiere zu `terminal.html`
2. **Risk Radar auswählen**: Klicke auf "Risk Radar" im Sidebar
3. **Daten laden**: Automatisches Laden beim ersten Öffnen
4. **Refresh**: Klicke auf "REFRESH" Button für aktuelle Daten

## Frontend Komponenten

### Main Dashboard
- **Current Status Cards**: Aktuelles Regime, Composite Z-Score, Last Update
- **Stress Indicators Grid**: Einzelne Z-Score Komponenten
- **Chart**: 6-Monats Historie mit Schwellenwerten
- **Thresholds Info**: Regime-Schwellenwerte Übersicht

### Recent Alerts Table
- Datum, Regime, Composite Z-Score
- Letzte 10 Regime-Wechsel
- Farbcodierung nach Severity

### Regime Statistics
- Verteilung (CALM, WATCH, WARNING, ALERT)
- Prozentuale Anteile der letzten 12 Monate
- Composite Z-Score Statistiken

## Datenquellen

**FRED (Federal Reserve Economic Data)**
- Datenquelle: https://fred.stlouisfed.org/
- Update-Frequenz: Täglich (je nach Indikator)
- Historische Daten: Ab 2010

**Indikatoren:**
- `BAMLH0A0HYM2`: ICE BofA US High Yield Index Option-Adjusted Spread
- `BAMLC0A0CM`: ICE BofA US Corporate Index Option-Adjusted Spread
- `STLFSI4`: St. Louis Fed Financial Stress Index
- `VIXCLS`: CBOE Volatility Index (VIX)

## Erweiterungen & Anpassungen

### Indikatoren hinzufügen
In `backend.py` -> `get_risk_radar()`:
```python
series_config = {
    'BAMLH0A0HYM2': 'HY_OAS',
    'BAMLC0A0CM': 'IG_OAS',
    'STLFSI4': 'STLFSI',
    'VIXCLS': 'VIX',
    'NEW_SERIES_ID': 'NEW_NAME'  # Hier hinzufügen
}

base_weights = {
    "HY_OAS_Z": 0.30,
    "IG_OAS_Z": 0.20,
    "STLFSI_Z": 0.25,
    "VIX_Z": 0.25,
    "NEW_NAME_Z": 0.10  # Gewichtung anpassen
}
```

### Schwellenwerte anpassen
In `backend.py` -> `classify_regime()`:
```python
if cs >= 2.5:  # ALERT Schwellenwert
    return "ALERT"
elif cs >= 1.75:  # WARNING Schwellenwert
    return "WARNING"
elif cs >= 1.0:  # WATCH Schwellenwert
    return "WATCH"
```

### Lookback-Periode ändern
```python
lookback = 252  # 1 Jahr (252 Handelstage)
lookback = 126  # 6 Monate
lookback = 63   # 3 Monate
```

## Performance

- **API Response Zeit**: ~2-5 Sekunden (abhängig von FRED API)
- **Daten Caching**: Nicht implementiert (jeder Request lädt fresh data)
- **Chart Rendering**: ~100-200ms (130 Datenpunkte)

### Performance Optimierung
Für Production empfohlen:
1. **Caching**: Redis oder Memcached für FRED Daten (15 Minuten TTL)
2. **Background Jobs**: Periodische Datenaktualisierung (z.B. alle 15 Min.)
3. **Data Preloading**: Beim Server-Start historische Daten laden

## Troubleshooting

### Problem: "fredapi not installed"
**Lösung:**
```bash
pip install fredapi
```

### Problem: "FRED API rate limit exceeded"
**Lösung:**
- FRED Free Tier: 1000 requests/day
- Implementiere Caching
- Verwende eigenen API Key

### Problem: "No data available"
**Mögliche Ursachen:**
1. FRED API down (selten)
2. Indikator-ID falsch
3. Datum-Range außerhalb verfügbarer Daten

**Check:**
```python
from fredapi import Fred
fred = Fred(api_key="your_key")
data = fred.get_series('BAMLH0A0HYM2')
print(data.tail())
```

### Problem: Chart wird nicht angezeigt
**Lösung:**
1. Browser Console prüfen (F12)
2. Chart.js Library geladen? -> `<script src="https://cdn.jsdelivr.net/npm/chart.js..."></script>`
3. Canvas Element vorhanden? -> `<canvas id="riskRadarChart"></canvas>`

## Deployment

### Railway / Heroku
1. `requirements.txt` enthält bereits `fredapi==0.5.2`
2. Environment Variable setzen: `FRED_API_KEY=your_key`
3. Standard Deployment-Prozess

### Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FRED_API_KEY=your_key_here
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Credits

- **Original Konzept**: Risk Radar Jupyter Notebooks (HTF & LTF)
- **Integration**: Atlas Terminal V1.1.1
- **Datenquelle**: Federal Reserve Economic Data (FRED)
- **Chart Library**: Chart.js v4.4.0

## Changelog

### V1.0 (2025-10-12)
- Initial Integration
- 4 Basis-Indikatoren (HY_OAS, IG_OAS, STLFSI, VIX)
- Composite Z-Score Berechnung
- Regime-Klassifikation (CALM, WATCH, WARNING, ALERT)
- Chart.js Visualisierung
- Recent Alerts Table
- Regime Statistics Dashboard

## Roadmap

### Geplante Features
- [ ] Caching-Implementierung (Redis)
- [ ] Background Job für Daten-Updates
- [ ] Email/Push Alerts bei Regime-Wechsel
- [ ] Multi-Timeframe Analyse (HTF/LTF Switch)
- [ ] Additional Indicators (Credit Spreads, Treasury Rates)
- [ ] Export Functionality (CSV, PDF Reports)
- [ ] Historical Backtest gegen S&P 500 Drawdowns

## Lizenz

Teil von Atlas Terminal V1.1.1
