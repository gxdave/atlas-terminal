# Atlas Terminal - Yahoo Finance API Fix für Railway Deployment

## Problem
Yahoo Finance blockiert häufig Anfragen von Cloud-Hosting-Diensten wie Railway, was zu folgenden Fehlern führt:
```
ERROR:yfinance:Failed to get ticker 'EURUSD=X' reason: Expecting value: line 1 column 1 (char 0)
```

## Implementierte Lösungen

### 1. **Erweiterte HTTP-Headers** ✅
- Rotation mehrerer realistischer User-Agent-Strings
- Vollständige Browser-Header (Accept, Accept-Language, etc.)
- Cache-Control und DNT-Header

### 2. **Retry-Mechanismus** ✅
- 3 Versuche pro Symbol-Variante
- 2 Sekunden Delay zwischen Retries
- Timeout von 10 Sekunden pro Request

### 3. **Alternative Datenquellen** ✅
- **Alpha Vantage API** - Primärer Fallback (100% kostenlos, 25 Requests/Tag)
- **Twelve Data API** - Sekundärer Fallback
- **Yahoo Finance Download** - Tertiärer Fallback
- Automatischer Fallback wenn Yahoo Finance fehlschlägt

### 4. **Symbol-Aliase** ✅
- Mehrere Symbol-Varianten werden getestet (z.B. `EURUSD=X` und `EUR=X`)

## Deployment auf Railway

### Schritt 1: Alpha Vantage API-Key erstellen (KOSTENLOS! ⚡)

**WICHTIG:** Da Yahoo Finance Railway komplett blockiert, brauchst du einen Alpha Vantage API-Key:

1. Gehe zu: **https://www.alphavantage.co/support/#api-key**
2. Gib deine E-Mail ein
3. Klicke **"GET FREE API KEY"**
4. Kopiere den API-Key (Format: `ABC123XYZ456`)

**Kosten:** 100% KOSTENLOS, keine Kreditkarte nötig!
**Limit:** 25 Requests/Tag (ausreichend für Testing)
**Alternative:** Twelve Data bietet 800 Requests/Tag kostenlos

### Schritt 2: Railway Environment Variables setzen

1. Gehe zu deinem Railway Projekt Dashboard
2. Klicke auf **"Variables"** Tab
3. Füge hinzu:
```
ALPHAVANTAGE_API_KEY=dein_api_key_hier
```

Optional (für News Feature):
```
NEWS_API_KEY=your_newsapi_key_here
```

### Schritt 3: Code aktualisieren und pushen
```bash
cd "/Users/davidgauch/Library/CloudStorage/OneDrive-Persönlich/Desktop/Coding/Atlas Terminal/V1.1.1"
git add backend.py DEPLOYMENT_FIX.md
git commit -m "Fix: Add Alpha Vantage fallback for Railway deployment"
git push origin main
```

### Schritt 4: Railway Redeploy überprüfen
Railway deployed automatisch. Prüfe die Logs:
```bash
railway logs --tail
```

## Wenn das Problem weiterhin besteht

### Option A: VPN/Proxy verwenden
Railway erlaubt Custom Proxies. Du könntest einen Proxy-Service hinzufügen:
```python
session.proxies = {
    'http': 'http://proxy-server:port',
    'https': 'https://proxy-server:port'
}
```

### Option B: Bezahlte API nutzen
Falls Yahoo Finance dauerhaft blockiert:

1. **Alpha Vantage** (kostenlos 25 requests/Tag)
   - Registrieren: https://www.alphavantage.co/support/#api-key
   - API-Key in Railway Environment Variables hinzufügen

2. **Twelve Data** (kostenlos 800 requests/Tag)
   - Registrieren: https://twelvedata.com/
   - API-Key in Railway Environment Variables hinzufügen

### Option C: Railway IP-Range whitelisten
Kontaktiere Yahoo Finance Support (unwahrscheinlich zu funktionieren)

## Testing

### Lokal testen:
```bash
cd "Atlas Terminal/V1.1.1"
python -m uvicorn backend:app --reload --port 8000
```

### Test-Request:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": ["Bullish", "Bearish", "Bullish"],
    "symbol": "EURUSD=X",
    "timeframe": "1d",
    "period": "5y"
  }'
```

## Erwartete Log-Ausgabe (Erfolg)

```
INFO:backend:Analyzing pattern ['Bullish', 'Bearish', 'Bullish'] for EURUSD=X
INFO:backend:Loading data for EURUSD=X with timeframe 1d
INFO:backend:Using enhanced headers for Railway compatibility
INFO:backend:Attempting to load: EURUSD=X
INFO:backend:Method 1: period=5y, interval=1d, auto_adjust=True
INFO:backend:Method 1 result: 1258 rows, empty=False
INFO:backend:✓ SUCCESS with EURUSD=X (Method 1)
INFO:backend:Date range: 2020-01-02 to 2025-01-10
INFO:backend:Successfully loaded 1258 candles
INFO:backend:Analysis complete: 42 matches found
INFO:     100.64.0.6:41230 - "POST /api/analyze HTTP/1.1" 200 OK
```

## Erwartete Log-Ausgabe (Fallback zu Alpha Vantage)

```
INFO:backend:Analyzing pattern ['Bullish', 'Bearish', 'Bullish'] for EURUSD=X
INFO:backend:Loading data for EURUSD=X with timeframe 1d
INFO:backend:Using enhanced headers for Railway compatibility
INFO:backend:Attempting to load: EURUSD=X
ERROR:yfinance:Failed to get ticker 'EURUSD=X' reason: Expecting value: line 1 column 1
WARNING:backend:Yahoo Finance failed for EURUSD=X. Trying alternative source...
INFO:backend:Trying alternative source: _try_alphavantage
INFO:backend:Alpha Vantage: Trying EURUSD with function FX_DAILY
INFO:backend:Alpha Vantage: SUCCESS - 1258 rows
INFO:backend:✓ SUCCESS with _try_alphavantage
INFO:backend:Successfully loaded 1258 candles
INFO:backend:Analysis complete: 42 matches found
INFO:     100.64.0.6:41230 - "POST /api/analyze HTTP/1.1" 200 OK
```

**WICHTIG:** Wenn du den Alpha Vantage API-Key nicht setzt, wird "demo" verwendet, was nur für IBM funktioniert!

## Support

Bei weiteren Problemen:
1. Railway Logs prüfen: `railway logs`
2. Stelle sicher, dass alle Dependencies installiert sind
3. Teste die API lokal vor dem Deployment
4. Prüfe Railway Service Status: https://status.railway.app/

## Weitere Optimierungen (Optional)

### Caching implementieren
```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_load_data(symbol, timeframe, cache_time):
    # cache_time = int(time.time() / 3600)  # Cache für 1 Stunde
    return analyzer_instance.load_data(symbol, timeframe)
```

### Rate Limiting hinzufügen
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/analyze")
@limiter.limit("10/minute")
async def analyze_pattern(request: PatternRequest):
    ...
```
