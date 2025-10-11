# SCHNELL-FIX: Yahoo Finance Blockierung auf Railway

## Problem
Railway wird von Yahoo Finance geblockt → "Expecting value: line 1 column 1 (char 0)"

## Lösung in 3 Schritten

### 1️⃣ Alpha Vantage API-Key holen (2 Minuten)
Gehe zu: https://www.alphavantage.co/support/#api-key
- Email eingeben
- "GET FREE API KEY" klicken
- Key kopieren (z.B. `ABC123XYZ456`)

**Kosten:** KOSTENLOS (kein Credit Card nötig!)

### 2️⃣ Key in Railway eintragen (1 Minute)
Railway Dashboard → Dein Projekt → Tab "Variables" → Hinzufügen:
```
ALPHAVANTAGE_API_KEY=dein_key_hier
```

### 3️⃣ Code deployen
```bash
cd "/Users/davidgauch/Library/CloudStorage/OneDrive-Persönlich/Desktop/Coding/Atlas Terminal/V1.1.1"
git add .
git commit -m "Fix: Add Alpha Vantage fallback"
git push origin main
```

## Fertig! ✅

Die App verwendet jetzt:
1. **Yahoo Finance** (Primary - wenn verfügbar)
2. **Alpha Vantage** (Fallback - funktioniert auf Railway)
3. **Twelve Data** (Fallback 2)

## Testen
Nach dem Deployment prüfen:
```bash
railway logs --tail
```

Du solltest sehen:
```
INFO: Alpha Vantage: SUCCESS - 1258 rows
```

## Alternative: Twelve Data (mehr Requests)
Falls du mehr als 25 Requests/Tag brauchst:
- https://twelvedata.com/ (800 Requests/Tag kostenlos)
- API-Key in Railway als `TWELVEDATA_API_KEY` hinzufügen

## Hilfe
Probleme? Siehe DEPLOYMENT_FIX.md für Details.
