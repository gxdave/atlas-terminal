# Railway Deployment Guide - Atlas Terminal v1.1.1

## ✅ Vorbereitung abgeschlossen

Dein Atlas Terminal ist jetzt bereit für das Deployment auf Railway! Alle notwendigen Dateien sind vorhanden und committed.

## 📋 Voraussetzungen

- Railway Account (https://railway.app)
- GitHub Repository ist bereits verbunden
- Alle Änderungen sind committed und gepusht ✅

## 🚀 Railway Deployment Schritte

### 1. Railway Projekt erstellen

1. Gehe zu https://railway.app
2. Klicke auf **"New Project"**
3. Wähle **"Deploy from GitHub repo"**
4. Wähle dein Repository: **gxdave/atlas-terminal**

### 2. Projekt Konfiguration

Railway erkennt automatisch deine `railway.json` Konfiguration:
- Build Command: Automatisch via Nixpacks
- Start Command: `uvicorn backend:app --host 0.0.0.0 --port $PORT`

### 3. Umgebungsvariablen (Optional)

Falls du später zusätzliche APIs integrieren möchtest:

```bash
# FRED API für Economic Data (optional)
FRED_API_KEY=dein_fred_api_key

# Alpha Vantage für zusätzliche Marktdaten (optional)
ALPHA_VANTAGE_API_KEY=dein_alpha_vantage_key

# Twelve Data für Forex (optional)
TWELVE_DATA_API_KEY=dein_twelve_data_key
```

### 4. Domain Setup

Nach dem Deployment erhältst du eine Railway URL wie:
```
https://atlas-terminal-production.up.railway.app
```

Du kannst auch eine Custom Domain hinzufügen:
1. Gehe zu Settings → Domains
2. Füge deine Domain hinzu
3. Konfiguriere DNS Records

## 🔧 Was wurde deployed?

### ✅ Backend Features
- FastAPI Server mit CORS
- User Authentication & Authorization
- Market Data API (yfinance)
- **NEU: Sentiment Analysis API** (`/api/sentiment`)
- Risk Radar
- Economic Data
- COT Data
- News Feed
- Watchlist Management

### ✅ Frontend Features
- Dashboard
- Probability Analyzer
- Risk Radar
- Markets (TradingView Charts)
- Economic Data
- Institutional Positioning
- **NEU: Sentiment View mit Risk On/Off Gauges**
- Portfolio (Coming Soon)
- User Profile

### 🎯 Sentiment Analysis Details

Das neue Sentiment Feature bietet:
- **3 Timeframes**: Daily, Weekly, Monthly
- **Live Marktdaten**: VIX, S&P 500, Gold, DXY
- **Visuelle Gauges**: Risk Off (rot) bis Risk On (grün)
- **Key Indicators**:
  - VIX Index (Volatilität)
  - SPX Performance
  - Gold/SPX Ratio
  - USD Strength (DXY)
  - HY Spreads
  - Crypto Fear & Greed

## 📊 API Endpoints

Deine deployed App stellt folgende Endpoints bereit:

```
GET /                           # Landing Page
GET /login.html                 # Login
GET /terminal.html              # Terminal Interface
GET /admin.html                 # Admin Panel

# Authentication
POST /api/auth/login            # User Login
GET /api/auth/me                # Current User

# Market Data
GET /api/market-data/{symbol}   # Symbol Data
GET /api/assets                 # Available Assets
GET /api/timeframes             # Available Timeframes

# Analysis
GET /api/risk-radar             # Risk Radar Data
GET /api/sentiment              # 🆕 Sentiment Analysis
GET /api/cot-data               # COT Data
GET /api/economic/{country}     # Economic Calendar

# User Data
GET /api/user/watchlist         # User Watchlist
POST /api/user/watchlist        # Add to Watchlist
GET /api/user/widgets           # Dashboard Widgets

# Admin
GET /api/admin/users            # User Management
POST /api/admin/users           # Create User
DELETE /api/admin/users/{username}  # Delete User
```

## 🔐 Sicherheit

### Admin User Setup
Beim ersten Deployment wird automatisch ein Admin User erstellt:
- Username: `admin`
- Password: `admin123` (⚠️ **BITTE SOFORT ÄNDERN!**)

### Erste Schritte nach Deployment:
1. Login als Admin
2. Ändere das Admin Passwort
3. Erstelle zusätzliche User
4. Teste alle Features

## 📝 Monitoring

Railway bietet automatisches Monitoring:
- **Logs**: Sieh dir Echtzeit-Logs an
- **Metrics**: CPU, Memory, Network Usage
- **Health Check**: `/health` endpoint

## 🐛 Troubleshooting

### Problem: Deployment failed
**Lösung**: Prüfe die Logs in Railway Dashboard

### Problem: Database nicht initialisiert
**Lösung**: Die SQLite Datenbank wird automatisch beim ersten Start erstellt

### Problem: Sentiment Daten laden nicht
**Lösung**:
- Prüfe ob yfinance Zugriff hat
- Railway hat manchmal Rate Limits für externe APIs
- Alternative: Caching implementieren

### Problem: CORS Errors
**Lösung**: CORS ist bereits konfiguriert (`allow_origins=["*"]`)

## 🚀 Deployment Check

Nach dem Deployment teste folgende URLs:

```bash
# Health Check
curl https://deine-app.railway.app/health

# Sentiment API
curl https://deine-app.railway.app/api/sentiment

# Landing Page
https://deine-app.railway.app
```

## 📈 Nächste Schritte

1. **Performance Optimierung**
   - Caching für Sentiment-Daten implementieren
   - Response-Zeit optimieren

2. **Feature Enhancements**
   - Real-time updates via WebSockets
   - Zusätzliche Sentiment-Indikatoren
   - Alert System für extreme Risk On/Off Levels

3. **Monitoring**
   - Error Tracking (z.B. Sentry)
   - Analytics (z.B. Google Analytics)
   - Uptime Monitoring

## 💡 Tipps

- Railway bietet **$5 Free Credits** pro Monat
- Nutze **Environment Variables** für sensitive Daten
- Aktiviere **Auto-Deploy** für automatische Updates bei Git Push
- Nutze **Rollback** bei Problemen

## 📞 Support

Bei Fragen oder Problemen:
1. Prüfe Railway Logs
2. Siehe Backend Logs für API Errors
3. Browser Console für Frontend Errors

---

**Viel Erfolg mit deinem Atlas Terminal Deployment! 🎉**

Erstellt mit [Claude Code](https://claude.com/claude-code)
