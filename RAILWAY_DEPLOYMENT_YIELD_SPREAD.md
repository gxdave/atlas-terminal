# Railway Deployment Guide - Yield Spread Analyzer

## Übersicht

Dieser Guide zeigt, wie du den Yield Spread Analyzer mit FRED API Integration auf Railway deployst.

---

## Voraussetzungen

1. **Railway Account**: [railway.app](https://railway.app)
2. **FRED API Key**: [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
3. **GitHub Repository** (optional): Für automatisches Deployment

---

## Schritt 1: FRED API Key erhalten

1. Gehe zu: https://fred.stlouisfed.org/docs/api/api_key.html
2. Erstelle einen kostenlosen Account
3. Beantrage einen API Key
4. Kopiere den API Key (Format: `abcdef1234567890abcdef1234567890`)

---

## Schritt 2: Railway Projekt vorbereiten

### Option A: GitHub Deployment (empfohlen)

1. **Push Code zu GitHub:**
   ```bash
   cd "Atlas Terminal/V1.1.1"
   git add .
   git commit -m "Add Yield Spread Analyzer with FRED API"
   git push origin main
   ```

2. **Railway Projekt erstellen:**
   - Gehe zu [railway.app](https://railway.app)
   - Click "New Project"
   - Wähle "Deploy from GitHub repo"
   - Wähle dein Repository
   - Railway erkennt automatisch die Python-App

### Option B: CLI Deployment

1. **Railway CLI installieren:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Projekt initialisieren:**
   ```bash
   cd "Atlas Terminal/V1.1.1"
   railway init
   ```

4. **Deployen:**
   ```bash
   railway up
   ```

---

## Schritt 3: Environment Variables konfigurieren

### Via Railway Dashboard

1. Gehe zu deinem Railway Projekt
2. Click auf "Variables"
3. Füge folgende Variable hinzu:

   **FRED_API_KEY**
   ```
   [Dein FRED API Key]
   ```

4. Optional weitere Variables:
   ```
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

### Via Railway CLI

```bash
railway variables set FRED_API_KEY="your_fred_api_key_here"
```

---

## Schritt 4: Deployment verifizieren

1. **Check Logs:**
   ```bash
   railway logs
   ```

   Suche nach:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:yield_spread_analyzer:FRED API initialized successfully
   ```

2. **Test API:**
   - Öffne: `https://your-app.railway.app/health`
   - Should return: `{"status":"healthy","timestamp":"..."}`

3. **Test Yield Spread Endpoint:**
   - Login im Frontend
   - Gehe zu "Yield Spread Analyzer"
   - Klicke "ANALYZE"
   - Check Browser Console für FRED API Logs

---

## Schritt 5: International Yields testen

Nach erfolgreichem Deployment solltest du internationale Spreads sehen:

### Erwartete Spreads:
- ✅ **US_10Y_2Y** (US Yield Curve)
- ✅ **US_EU_10Y** (US vs Germany 10Y)
- ✅ **US_UK_10Y** (US vs UK 10Y)
- ✅ **US_JP_10Y** (US vs Japan 10Y)

### Wenn keine internationalen Spreads angezeigt werden:

1. **Check FRED API Key:**
   ```bash
   railway variables
   ```
   Stelle sicher, dass `FRED_API_KEY` gesetzt ist

2. **Check Logs:**
   ```bash
   railway logs --filter "FRED"
   ```

   Mögliche Errors:
   - `Failed to initialize FRED API` → API Key falsch
   - `No international yields fetched` → FRED API Limit erreicht
   - `Failed to fetch [series]` → Falsche Series ID

3. **FRED API Limits:**
   - Free Tier: 120 Requests / Minute
   - Bei Überschreitung: Warte 1 Minute

---

## Troubleshooting

### Problem: "No FRED API key provided"

**Lösung:**
```bash
railway variables set FRED_API_KEY="your_key_here"
railway up --detach
```

### Problem: "Failed to fetch international yields"

**Mögliche Ursachen:**
1. FRED API Key ungültig
2. FRED API Rate Limit
3. Series ID nicht verfügbar

**Lösung:**
```bash
# Check API Key
railway variables

# Check Logs
railway logs --filter "international"

# Restart Service
railway restart
```

### Problem: "Module 'fredapi' not found"

**Lösung:**
```bash
# Stelle sicher, dass requirements.txt aktuell ist
cat requirements.txt | grep fredapi

# Falls nicht vorhanden:
echo "fredapi==0.5.2" >> requirements.txt
git add requirements.txt
git commit -m "Add fredapi dependency"
git push

# Railway wird automatisch neu deployen
```

---

## Performance Optimierung

### Caching

Der Analyzer implementiert bereits Caching für Performance:

```python
self.cache = {}
self.last_update = None
```

### Rate Limiting

FRED API hat folgende Limits:
- **Free Tier**: 120 Requests/Minute
- **Pro Tier**: 1000 Requests/Minute

**Best Practice:**
- Cache Daten für mindestens 15 Minuten
- Implement Request Batching
- Use `observation_start` und `observation_end` für gezielten Abruf

---

## Monitoring

### Health Check

Railway bietet automatische Health Checks:

```bash
railway healthcheck add --path /health --interval 60
```

### Logs

```bash
# Alle Logs
railway logs

# Filter für Yield Spread
railway logs --filter "yield"

# Filter für Errors
railway logs --filter "error"

# Live Logs
railway logs --follow
```

### Metrics

Im Railway Dashboard:
- CPU Usage
- Memory Usage
- Request Count
- Response Time

---

## Kosten

### Railway Free Tier
- $5 free credits/month
- Ausreichend für:
  - ~550 Stunden/Monat Runtime
  - Moderate API Usage

### FRED API
- Free Tier: Unbegrenzte Requests (mit Rate Limit)
- Keine Kosten

**Geschätzte monatliche Kosten:** $0 - $5

---

## Weitere Konfiguration

### Custom Domain

```bash
railway domain add your-domain.com
```

### Automatic Deployments

Railway deployt automatisch bei jedem Git Push (wenn GitHub connected).

**Disable Auto Deploy:**
```bash
railway settings set --auto-deploy=false
```

### Database Backup

```bash
# Download database
railway run bash -c "cat atlas_users.db" > atlas_users_backup.db
```

---

## Support

### Railway Support
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway

### FRED API Support
- Docs: https://fred.stlouisfed.org/docs/api/
- Email: api@stlouisfed.org

### Atlas Terminal Issues
- GitHub: [Your Repo]/issues

---

## Deployment Checklist

Vor dem Deployment:

- [ ] FRED API Key erhalten
- [ ] `requirements.txt` enthält `fredapi==0.5.2`
- [ ] Code committet und gepushed
- [ ] Railway Projekt erstellt
- [ ] Environment Variable `FRED_API_KEY` gesetzt
- [ ] Deployment erfolgreich
- [ ] Health Check passed (`/health`)
- [ ] Login funktioniert
- [ ] Yield Spread Analyzer sichtbar in Navigation
- [ ] ANALYZE Button funktioniert
- [ ] Internationale Spreads werden angezeigt
- [ ] Logs zeigen "FRED API initialized successfully"

---

**Stand:** 2. Dezember 2025
**Version:** Atlas Terminal v1.1.2 mit Yield Spread Analyzer
