# Railway Deployment Checklist - Yield Spread Analyzer

## Pre-Deployment

### 1. FRED API Key
- [ ] FRED Account erstellt: https://fred.stlouisfed.org
- [ ] API Key beantragt und erhalten
- [ ] API Key kopiert (Format: 32-stelliger alphanumerischer String)

### 2. Code Vorbereitung
- [x] `yield_spread_analyzer.py` erstellt
- [x] FRED API Integration implementiert
- [x] Backend API Endpunkte hinzugefügt
- [x] Frontend View erstellt
- [x] Navigation aktualisiert
- [x] `requirements.txt` aktualisiert (scipy, fredapi)
- [x] Syntax-Checks durchgeführt

### 3. Git Repository
- [ ] Alle Änderungen committet
  ```bash
  git add .
  git commit -m "Add Yield Spread Analyzer with FRED API integration"
  ```
- [ ] Code zu GitHub gepusht
  ```bash
  git push origin main
  ```

---

## Railway Setup

### 1. Projekt erstellen/verbinden
- [ ] Railway Account: https://railway.app
- [ ] Projekt erstellt oder bestehendes ausgewählt
- [ ] GitHub Repository verbunden (falls nicht CLI)

### 2. Environment Variables
- [ ] `FRED_API_KEY` gesetzt in Railway Dashboard
  - Gehe zu: Project → Variables → + New Variable
  - Name: `FRED_API_KEY`
  - Value: [Dein API Key]

### 3. Deployment
- [ ] Code deployt (automatisch via GitHub oder `railway up`)
- [ ] Build erfolgreich
- [ ] Service läuft (grüner Status)

---

## Verification

### 1. Health Check
- [ ] Health Endpoint erreichbar: `https://your-app.railway.app/health`
- [ ] Response: `{"status":"healthy","timestamp":"..."}`

### 2. Logs prüfen
```bash
railway logs
```

Erwartete Log-Einträge:
- [ ] `INFO:     Started server process`
- [ ] `INFO:     Application startup complete.`
- [ ] `INFO:yield_spread_analyzer:FRED API initialized successfully`
- [ ] KEINE Errors bzgl. FRED API Key

### 3. Frontend Tests
- [ ] Login funktioniert
- [ ] Navigation zeigt "Yield Spread Analyzer"
- [ ] View öffnet sich ohne Fehler
- [ ] Period Selection funktioniert
- [ ] "ANALYZE" Button lädt Daten

### 4. Data Verification
Nach Klick auf "ANALYZE":

#### Current Market Snapshot
- [ ] US Treasury Yields angezeigt (US_2Y, US_10Y, US_30Y)
- [ ] FX Data angezeigt (DXY, EURUSD, USDJPY, GBPUSD)
- [ ] Spreads angezeigt:
  - [ ] **US_10Y_2Y** (immer)
  - [ ] **US_EU_10Y** (wenn FRED funktioniert)
  - [ ] **US_UK_10Y** (wenn FRED funktioniert)
  - [ ] **US_JP_10Y** (wenn FRED funktioniert)

#### Charts
- [ ] DXY-Linie sichtbar (orange)
- [ ] US_10Y_2Y Spread sichtbar (blau)
- [ ] Internationale Spreads sichtbar (falls FRED OK)

#### Correlation Matrix
- [ ] Tabelle zeigt Spreads × FX Pairs
- [ ] Werte zwischen -1 und 1
- [ ] Farbcodierung funktioniert

#### Lead/Lag Analysis
- [ ] Tabelle zeigt Lag-Werte
- [ ] Interpretation sinnvoll

#### Statistical Analysis
- [ ] Z-Scores angezeigt
- [ ] Werte im erwarteten Bereich (-3 bis +3)

---

## Troubleshooting

### Problem: Keine internationalen Spreads

**Check 1: FRED API Key**
```bash
railway variables
```
- [ ] `FRED_API_KEY` ist gesetzt
- [ ] Wert ist korrekt (32 Zeichen)

**Check 2: Logs**
```bash
railway logs --filter "FRED"
```
- [ ] "FRED API initialized successfully" vorhanden
- [ ] KEINE "Failed to initialize FRED API"
- [ ] KEINE "No FRED API key provided"

**Check 3: Browser Console**
- [ ] Öffne Developer Tools (F12)
- [ ] Tab "Console"
- [ ] Suche nach FRED-bezogenen Meldungen
- [ ] Prüfe API Response im "Network" Tab

### Problem: "Module 'fredapi' not found"

**Lösung:**
```bash
# Check requirements.txt
cat requirements.txt | grep fredapi

# Falls fehlt:
echo "fredapi==0.5.2" >> requirements.txt
git add requirements.txt
git commit -m "Add fredapi dependency"
git push

# Railway deployt automatisch neu
```

### Problem: Rate Limit exceeded

**Symptom:**
- Logs zeigen HTTP 429 Errors
- Manche Daten fehlen

**Lösung:**
- Warte 1 Minute
- Refresh die Seite
- FRED Free Tier: 120 Requests/Minute

### Problem: Deployment failed

**Check Build Logs:**
```bash
railway logs --build
```

**Häufige Ursachen:**
- Syntax-Error in Python
- Fehlende Dependency in requirements.txt
- Port-Konflikt

---

## Post-Deployment

### 1. Performance Monitoring
- [ ] Railway Dashboard → Metrics
- [ ] CPU Usage < 50%
- [ ] Memory Usage < 500MB
- [ ] Response Time < 5s

### 2. Error Monitoring
```bash
# Live Logs
railway logs --follow

# Filter Errors
railway logs --filter "error"
```

### 3. User Testing
- [ ] Verschiedene Zeiträume testen (1mo, 3mo, 6mo, 1y)
- [ ] Mehrfache Analysen durchführen
- [ ] Different FX Pairs prüfen
- [ ] Alerts überprüfen (bei Curve Inversion, etc.)

---

## Rollback Plan

Falls Probleme auftreten:

### Option 1: Environment Variable zurücksetzen
```bash
railway variables set FRED_API_KEY=""
```
→ Tool funktioniert ohne internationale Yields

### Option 2: Vorherige Version deployen
```bash
git revert HEAD
git push
```
→ Railway deployt automatisch zurück

### Option 3: Service neu starten
```bash
railway restart
```

---

## Success Criteria

✅ **Deployment erfolgreich wenn:**

1. Health Endpoint antwortet
2. Login funktioniert
3. Yield Spread Analyzer lädt
4. US Yields und Spreads angezeigt
5. Internationale Spreads angezeigt (EU, UK, JP)
6. Charts rendern korrekt
7. Correlation Matrix zeigt Daten
8. Lead/Lag Analysis zeigt Daten
9. Z-Scores berechnet
10. Logs zeigen "FRED API initialized successfully"
11. Keine Errors in Browser Console
12. Performance akzeptabel (< 5s Ladezeit)

---

## Kosten-Check

### Railway
- Free Tier: $5/Monat Credits
- Geschätzt: ~$2-3/Monat für Atlas Terminal

### FRED API
- Free Tier: Unbegrenzt (mit Rate Limit)
- Kosten: $0

**Total:** ~$2-3/Monat

---

## Support Kontakte

### Railway
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### FRED API
- Docs: https://fred.stlouisfed.org/docs/api/
- Support: api@stlouisfed.org
- Status: https://fred.stlouisfed.org/docs/api/api_status.html

---

## Nächste Schritte nach Deployment

1. **Monitor für 24h:**
   - Logs auf Errors prüfen
   - Performance Metrics checken
   - User Feedback sammeln

2. **Optimierungen (optional):**
   - Caching implementieren
   - Request Batching für FRED API
   - Additional spreads hinzufügen

3. **Dokumentation:**
   - User Guide für Yield Spread Analyzer
   - Video-Tutorial (optional)
   - FAQ basierend auf User-Fragen

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Railway URL:** _______________
**Status:** ⬜ Pending / ⬜ Deployed / ⬜ Verified

---

*Letzte Aktualisierung: 2. Dezember 2025*
