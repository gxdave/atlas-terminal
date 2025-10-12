# Symbol Fallback System - Atlas Terminal

## Übersicht

Das Atlas Terminal nutzt **mehrere Datenquellen** für maximale Zuverlässigkeit:

1. **Yahoo Finance** (primär via yfinance)
2. **Yahoo Finance Download** (alternatives yfinance Interface)
3. **Twelve Data API** (Forex & Indizes)
4. **Alpha Vantage API** (alle Asset-Klassen)

## Symbol-Konvertierung

Verschiedene Datenquellen verwenden unterschiedliche Symbol-Formate:

### Forex (FX-Paare)
| Asset | Yahoo Finance | Alpha Vantage | Twelve Data |
|-------|--------------|---------------|-------------|
| EUR/USD | EURUSD=X | EURUSD | EUR/USD |
| GBP/USD | GBPUSD=X | GBPUSD | GBP/USD |
| USD/JPY | USDJPY=X | USDJPY | USD/JPY |

### Commodities (Rohstoffe)
| Asset | Yahoo Finance | Alpha Vantage | Twelve Data |
|-------|--------------|---------------|-------------|
| Gold | GC=F | GC | GC |
| Crude Oil | CL=F | CL | CL |
| Silver | SI=F | SI | SI |

### Indizes
| Asset | Yahoo Finance | Alpha Vantage | Twelve Data |
|-------|--------------|---------------|-------------|
| S&P 500 | ^GSPC | SPX | SPX |
| Nasdaq 100 | ^NDX | NDX | NDX |
| Dow Jones | ^DJI | DJI | DJI |
| DAX | ^DAX | DAX | DAX |

### Aktien
| Asset | Yahoo Finance | Alpha Vantage | Twelve Data |
|-------|--------------|---------------|-------------|
| Apple | AAPL | AAPL | AAPL |
| Microsoft | MSFT | MSFT | MSFT |

## Fallback-Reihenfolge

Wenn Yahoo Finance fehlschlägt, versucht das System automatisch:

```
1. Yahoo Finance Ticker.history()
   ↓ (fails)
2. yfinance.download()
   ↓ (fails)
3. Twelve Data API
   ↓ (fails)
4. Alpha Vantage API
   ↓ (fails)
5. [Error: No data available]
```

## API-Schlüssel (optional)

### Alpha Vantage
- **Free Tier**: 25 Requests/Tag
- **Setup**: Environment Variable `ALPHAVANTAGE_API_KEY`
- **Registrierung**: https://www.alphavantage.co/support/#api-key

### Twelve Data
- **Free Tier**: 800 Requests/Tag
- **Setup**: Kein API Key für Basic Endpoints nötig
- **Registrierung** (optional): https://twelvedata.com/pricing

## Logging

Das System loggt detailliert, welche Datenquelle verwendet wurde:

```
INFO: Loading data for GC=F with timeframe 1d
INFO: Attempting to load: GC=F
INFO: ✗ FAILED: No data for GC=F
INFO: Yahoo Finance failed for GC=F. Trying alternative source...
INFO: Trying alternative source: _try_yahoo_csv
INFO: Yahoo download(): Trying GC=F
INFO: ✗ Exception for GC=F (attempt 1/3)
INFO: Trying alternative source: _try_twelvedata
INFO: Converted GC=F to Twelve Data format: GC
INFO: ✓ SUCCESS with _try_twelvedata
INFO: Successfully loaded 1247 candles
```

## Bekannte Einschränkungen

1. **Yahoo Finance Blocking**: Kann auf Railway/Cloud-Servern blockiert werden
2. **Rate Limits**: Alpha Vantage hat niedrige Free-Tier Limits
3. **Datenverfügbarkeit**: Nicht alle Symbole sind bei allen Quellen verfügbar
4. **Historische Daten**: Manche APIs haben kürzere History-Limits

## Troubleshooting

### Problem: "No data available for symbol"
**Lösung**:
- Prüfe, ob das Symbol in `SYMBOL_CONVERSIONS` definiert ist
- Füge ggf. Alpha Vantage API Key hinzu
- Prüfe Logs für Details

### Problem: "Rate limit exceeded"
**Lösung**:
- Warte 24h (Alpha Vantage Reset)
- Registriere zusätzliche API Keys
- Nutze Premium-Tier APIs

### Problem: Yahoo Finance 404/403 Errors
**Lösung**:
- System versucht automatisch alternative Quellen
- Kein Eingriff nötig - Fallback sollte funktionieren

## Erweiterte Konfiguration

### Eigene API Keys setzen (Railway)

```bash
# Railway CLI
railway variables set ALPHAVANTAGE_API_KEY=your_key_here
railway variables set TWELVEDATA_API_KEY=your_key_here
```

### Lokale Entwicklung

```bash
# .env Datei erstellen
ALPHAVANTAGE_API_KEY=your_key_here
TWELVEDATA_API_KEY=your_key_here
```

## Support

Bei Problemen:
1. Prüfe die Logs im Terminal/Railway Dashboard
2. Teste Symbol-Konvertierung mit `test_symbols.py`
3. Verifiziere API Key Setup (falls verwendet)
