# Yield Spread Analyzer - Documentation

## Übersicht

Der **Yield Spread Analyzer** ist ein professionelles Makro-Analyse-Tool, das die Beziehung zwischen Zinsdifferenzen (Yield Spreads) und der Stärke des US-Dollars (DXY bzw. USD-Paare) in Echtzeit messbar, sichtbar und auswertbar macht.

**Philosophie:** Neutral. Kalt. Objektiv. Keine Interpretation - nur Messung.

---

## Features

### 1. Relative Zinsdifferenz (Interest Rate Advantage)

Das Tool berechnet folgende Spreads:

#### US Yield Curve (aktuell implementiert)
- **US 10Y - US 2Y**: Zinskurve / Rezessionssignal

#### International Spreads (zukünftig via FRED API)
- **Short-End** (wichtigster Bereich für FX):
  - US 2Y - EU 2Y
  - US 2Y - UK 2Y
  - US 2Y - JP 2Y

- **Long-End** (Wachstums- und Risikoerwartung):
  - US 10Y - EU 10Y
  - US 10Y - UK 10Y
  - US 10Y - JP 10Y

**Interpretation:**
- Steigende US-Spreads → Steigende Attraktivität des USD
- Fallende US-Spreads → Abnehmende Attraktivität des USD

---

### 2. Dollar-Stärke / Marktreaktion

Das Tool integriert:

- **DXY** (Dollar Index)
- **Wichtige Währungspaare:**
  - EUR/USD
  - USD/JPY
  - GBP/USD
- **Risikoindikatoren:**
  - VIX (Volatilitätsindex)
  - S&P 500 (optional)

**Ziel:** Visuell und statistisch überprüfen, wie stark und wann der USD auf Spread-Veränderungen reagiert.

---

### 3. Statistische Auswertung

Das Tool berechnet automatisch:

#### Rolling Correlation
- Korrelation zwischen Spread und DXY/FX-Paaren
- Zeitfenster: **30 / 90 / 180 Tage**
- Basis: **Returns/Delta** (nicht Rohwerte, um Scheinkorrelationen zu vermeiden)

#### Lead/Lag Analyse
- Identifiziert, wer sich zuerst bewegt: Spread oder DXY
- Max. Lag: ±20 Tage
- Zeigt an, ob Spreads als Leading- oder Lagging-Indikator fungieren

#### Z-Score der Spreads
- Misst Extremzustände
- Normalisiert auf historische Mean/Std
- Zeigt über-/unterbewertete Positionen

#### Momentum (Veränderungsrate)
- Tägliche Veränderungen (Returns)
- Identifiziert Beschleunigung/Verlangsamung

---

## Datenquellen

### Aktuell implementiert (yfinance)
- US Treasury Yields:
  - `^IRX` - US 13-Week Treasury (Proxy für 2Y)
  - `^TNX` - US 10-Year Treasury
  - `^TYX` - US 30-Year Treasury
- FX:
  - `DX-Y.NYB` - Dollar Index (DXY)
  - `EURUSD=X`, `USDJPY=X`, `GBPUSD=X`
- Risk:
  - `^VIX` - Volatility Index
  - `^GSPC` - S&P 500

### Zukünftig (FRED API)
- Internationale Government Bonds:
  - Deutschland 2Y/10Y (EU-Proxy)
  - UK 2Y/10Y
  - Japan 2Y/10Y

---

## API Endpunkte

### 1. Comprehensive Analysis
```http
GET /api/yield-spread/analyze?period={period}
```

**Parameter:**
- `period`: Zeitraum (`1mo`, `3mo`, `6mo`, `1y`, `2y`)

**Response:**
```json
{
  "timestamp": "2025-12-02T...",
  "period": "1y",
  "current": {
    "yields": {"US_2Y": 4.5, "US_10Y": 4.3, ...},
    "fx": {"DXY": 103.5, "EURUSD": 1.08, ...},
    "spreads": {"US_10Y_2Y": -0.2},
    "spread_zscores": {"US_10Y_2Y": -1.5},
    "fx_zscores": {"DXY": 0.5, ...}
  },
  "correlations": {
    "US_10Y_2Y": {
      "DXY": {"30d": 0.65, "90d": 0.72, "180d": 0.68},
      "EURUSD": {"30d": -0.55, ...}
    }
  },
  "lead_lag": {
    "US_10Y_2Y": {
      "DXY": {"lag": -3, "correlation": 0.75}
    }
  },
  "historical": {
    "dates": ["2024-01-01", ...],
    "yields": {...},
    "spreads": {...},
    "fx": {...}
  },
  "alerts": [
    {
      "type": "CURVE_INVERSION",
      "severity": "HIGH",
      "message": "US Yield Curve Inverted: -0.20bp",
      "value": -0.2
    }
  ]
}
```

### 2. Quick Summary
```http
GET /api/yield-spread/summary
```

**Response:**
```json
{
  "timestamp": "2025-12-02T...",
  "yields": {
    "current": {"US_2Y": 4.5, ...},
    "change_1d": {"US_2Y": 0.02, ...}
  },
  "fx": {
    "current": {"DXY": 103.5, ...},
    "change_1d": {"DXY": 0.15, ...}
  },
  "spreads": {
    "current": {"US_10Y_2Y": -0.2},
    "change_1d": {"US_10Y_2Y": -0.05}
  }
}
```

---

## Frontend Integration

### Navigation
Das Tool ist als **"Yield Spread Analyzer"** im Atlas Terminal Sidebar integriert.

### Views

#### 1. Header Card
- Period Selection (1mo - 2y)
- Analyze Button
- Beschreibung der Philosophie

#### 2. Current Market Snapshot
- **Treasury Yields** (US 2Y, 10Y, 30Y)
- **FX & Risk** (DXY, EUR/USD, USD/JPY, GBP/USD, VIX, SPX)
- **Yield Spreads** (US 10Y-2Y) mit Z-Scores

#### 3. Alerts
- Yield Curve Inversion (HIGH severity)
- Extreme Z-Scores (MEDIUM/HIGH severity)
- High Correlations (LOW severity)

#### 4. Charts
- **Dual-Axis Chart:**
  - Y-Axis (links): DXY (Orange)
  - Y-Axis (rechts): Spreads (verschiedene Farben)
  - X-Axis: Zeitverlauf (180 Tage)

#### 5. Correlation Matrix
- Tabelle: Spread × FX-Pair × Time Windows (30/90/180d)
- Farbcodierung:
  - **Rot** (|r| > 0.7): Strong
  - **Orange** (|r| > 0.5): Moderate
  - **Grün** (|r| > 0.3): Weak
  - **Grau**: Negligible

#### 6. Lead/Lag Analysis
- Tabelle: Spread × FX-Pair
- Columns: Lag (Tage), Correlation, Interpretation
- Interpretation:
  - Negative Lag: Spread führt
  - Positive Lag: FX führt
  - Zero Lag: Synchron

#### 7. Statistical Analysis
- **Spread Z-Scores**
- **FX Z-Scores**
- Farbcodierung nach Extremwerten

---

## Interpretationslogik

Das Tool beantwortet folgende Fragen **objektiv**:

1. **Haben die USA derzeit einen signifikanten Zinsvorteil?**
   → Spread-Werte zeigen absolute Differenz

2. **Wird der USD aktuell durch Zinsdifferenzen getrieben oder durch Risiko (Risk-Off)?**
   → Correlation + VIX zeigen Zusammenhänge

3. **Bestätigt oder widerspricht der Spread der Bewegung im USD?**
   → Lead/Lag zeigt zeitliche Beziehung

4. **Ist die aktuelle Bewegung statistisch „normal" oder extrem?**
   → Z-Scores zeigen historische Einordnung

---

## Alert-System

### Alert Types

#### 1. CURVE_INVERSION
- **Trigger:** US 10Y-2Y < 0
- **Severity:** HIGH
- **Interpretation:** Rezessionssignal

#### 2. EXTREME_ZSCORE
- **Trigger:** |Z-Score| > 2.5
- **Severity:** HIGH (|Z| > 3) oder MEDIUM (2.5 < |Z| < 3)
- **Interpretation:** Extremwert, statistisch selten

#### 3. HIGH_CORRELATION
- **Trigger:** |Correlation| > 0.7
- **Severity:** LOW
- **Interpretation:** Starker Zusammenhang identifiziert

---

## Verwendung

### Für Trader

**Frage:** "Ist die USD-Bewegung fundamental unterstützt – oder nur emotional getrieben?"

**Antwort:**
- Spread ↑ + DXY ↑ + High Correlation → **Fundamental unterstützt**
- Spread ↓ + DXY ↑ + Low Correlation + VIX ↑ → **Risk-Off / emotional**

### Für Makro-Analysten

**Frage:** "Wann reagiert der Markt auf Zinsdifferenzen?"

**Antwort:**
- Lead/Lag Analyse zeigt zeitliche Beziehung
- Negative Lag → Spreads sind Leading Indicator
- Positive Lag → Spreads sind Lagging Indicator

---

## Technische Details

### Dependencies
```
pandas>=2.1.4
numpy>=1.26.3
yfinance>=0.2.36
scipy>=1.11.4
```

### Performance
- Daten-Cache: In-Memory
- Historical Lookback: 180 Tage (performance-optimiert)
- API Response Time: ~2-5 Sekunden (abhängig von yfinance)

### Error Handling
- Graceful degradation bei fehlenden Daten
- Fallback auf leere DataFrames
- Klare Error Messages im Frontend

---

## Roadmap

### Phase 1 (✅ Implementiert)
- US Treasury Yields via yfinance
- DXY + Major FX Pairs
- US Yield Curve (10Y-2Y)
- Rolling Correlation (30/90/180d)
- Lead/Lag Analysis
- Z-Score Calculation
- Alert System
- Frontend Dashboard

### Phase 2 (🔄 Geplant)
- **FRED API Integration:**
  - EU/UK/JP Government Bonds
  - International Spreads (US-EU, US-UK, US-JP)
- **Enhanced Visualizations:**
  - Heatmap für Correlation Matrix
  - Lead/Lag Chart
- **Historical Backtesting:**
  - Spread-Strategie-Backtesting
  - Performance Metrics

### Phase 3 (📋 Future)
- **Real-Time Streaming:**
  - WebSocket Integration
  - Live Updates (1min)
- **Machine Learning:**
  - Regime Detection
  - Spread Prediction
- **Export Funktionen:**
  - PDF Reports
  - CSV Export

---

## Hinweise

### Limitierungen
1. **yfinance Limitations:**
   - Keine echten 2Y Yields (Proxy: 13-Week Treasury)
   - Keine internationalen Yields
   - Rate Limits möglich

2. **Datenverfügbarkeit:**
   - Internationale Spreads benötigen FRED API Key
   - Historische Daten begrenzt auf yfinance-Verfügbarkeit

3. **Statistische Validität:**
   - Korrelation ≠ Kausalität
   - Z-Scores basieren auf historischen Daten
   - Lead/Lag kann sich über Zeit ändern

### Best Practices
1. **Zeitfenster-Auswahl:**
   - 30d: Short-term Trading
   - 90d: Medium-term Positioning
   - 180d: Long-term Macro View

2. **Interpretation:**
   - Immer mehrere Zeitfenster vergleichen
   - VIX + Correlation kombinieren (Risk-Off Detection)
   - Z-Scores im Kontext des Regimes interpretieren

3. **Alerts:**
   - HIGH: Sofortige Aufmerksamkeit
   - MEDIUM: Monitoring
   - LOW: Information

---

## Support & Contribution

### Bug Reports
Bitte öffne ein Issue auf GitHub mit:
- Fehlerbeschreibung
- Erwartetes vs. tatsächliches Verhalten
- API Response (falls relevant)

### Feature Requests
Neue Features können über GitHub Issues vorgeschlagen werden.

### Contact
Bei Fragen zum Tool: Siehe Atlas Terminal Documentation

---

**© 2025 Atlas Terminal - Yield Spread Analyzer v1.0**

*Neutral. Kalt. Objektiv.*
