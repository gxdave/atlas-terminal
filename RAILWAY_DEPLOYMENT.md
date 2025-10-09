# 🚀 Atlas Terminal - Railway Deployment Anleitung

## 📋 Voraussetzungen

- GitHub Account
- Railway Account (kostenlos bei https://railway.app)
- Git installiert auf deinem PC

---

## 🔧 Schritt 1: GitHub Repository erstellen

### 1.1 Neues Repository auf GitHub erstellen
1. Gehe zu https://github.com/new
2. Repository Name: `atlas-terminal`
3. Visibility: **Public** oder **Private** (egal)
4. **NICHT** README, .gitignore oder Lizenz hinzufügen (haben wir schon)
5. Klicke **Create repository**

### 1.2 Lokales Git Repository initialisieren

Öffne ein Terminal in: `C:\Users\dgauc\OneDrive\Desktop\Coding\Atlas Terminal\V1.1.1`

```bash
# Git initialisieren
git init

# Alle Dateien hinzufügen
git add .

# Ersten Commit erstellen
git commit -m "Initial commit: Atlas Terminal v1.1.1"

# GitHub Repository als Remote hinzufügen (ersetze USERNAME mit deinem GitHub Username)
git remote add origin https://github.com/USERNAME/atlas-terminal.git

# Code zu GitHub pushen
git branch -M main
git push -u origin main
```

---

## 🚂 Schritt 2: Railway Deployment

### 2.1 Railway Account erstellen
1. Gehe zu https://railway.app
2. Klicke **Login**
3. Login mit GitHub Account
4. Autorisiere Railway

### 2.2 Neues Projekt erstellen
1. Klicke **New Project**
2. Wähle **Deploy from GitHub repo**
3. Wähle dein `atlas-terminal` Repository
4. Klicke **Deploy Now**

### 2.3 Environment Variables konfigurieren (Optional)

Falls du einen NewsAPI Key hast:

1. Gehe zu deinem Projekt
2. Klicke auf **Variables**
3. Füge hinzu:
   - **Name**: `NEWS_API_KEY`
   - **Value**: Dein API Key von newsapi.org

**Wichtig:** Du musst dann den Code anpassen, um die Variable zu lesen:

In `backend.py` Zeile 337 ändern von:
```python
NEWS_API_KEY = "DEIN_API_KEY_HIER"
```

Zu:
```python
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "DEIN_API_KEY_HIER")
```

### 2.4 Domain erhalten

Nach erfolgreichem Deployment:

1. Railway generiert automatisch eine URL wie: `atlas-terminal-production.up.railway.app`
2. Diese URL findest du unter **Settings** → **Domains**
3. Kopiere diese URL

---

## 🌐 Schritt 3: Terminal öffnen

### Dein Terminal ist jetzt live! 🎉

**URLs:**
- **Landing Page**: `https://deine-railway-url.up.railway.app`
- **Terminal**: `https://deine-railway-url.up.railway.app/terminal.html`
- **API Docs**: `https://deine-railway-url.up.railway.app/docs`

---

## ✅ Schritt 4: Testen

1. Öffne die Landing Page
2. Klicke **Launch Terminal**
3. Teste alle Features:
   - ✅ Dashboard
   - ✅ Probability Analyzer
   - ✅ Markets (TradingView Charts)
   - ✅ News Feed
   - ✅ Portfolio (Coming Soon)
   - ✅ Profile (Coming Soon)

---

## 🔄 Updates deployen

Wenn du Änderungen machst:

```bash
# Änderungen committen
git add .
git commit -m "Update: Beschreibung der Änderung"

# Zu GitHub pushen
git push origin main
```

Railway deployed automatisch! ⚡

---

## 💰 Kosten

- **Railway Free Tier**: $5/Monat Guthaben gratis
- **Dein Projekt**: ~$1-2/Monat (24/7 läuft)
- **Erste Monate kostenlos** mit Gratis-Guthaben

---

## 🐛 Troubleshooting

### Problem: Deployment schlägt fehl
**Lösung**: Checke die Logs in Railway Dashboard

### Problem: Frontend kann Backend nicht erreichen
**Lösung**: Prüfe ob CORS richtig konfiguriert ist (ist bereits erledigt)

### Problem: News funktionieren nicht
**Lösung**:
- Entweder NewsAPI Key hinzufügen (siehe Schritt 2.3)
- Oder Mock-Daten werden automatisch verwendet

### Problem: Port 8000 bereits in Verwendung (lokal)
**Lösung**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# Oder einfach Port wechseln in backend.py
```

---

## 📊 Monitoring

### Railway Dashboard

- **Logs**: Echtzeit-Logs deiner App
- **Metrics**: CPU, RAM, Network Usage
- **Deploys**: History aller Deployments

---

## 🔒 Sicherheit

### Empfohlene Maßnahmen

1. **API Keys**: Nie im Code hardcoden, immer Environment Variables nutzen
2. **CORS**: Für Production spezifische Domains erlauben statt `*`
3. **Rate Limiting**: Bei öffentlicher Nutzung implementieren

### CORS für Production anpassen

In `backend.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://deine-railway-url.up.railway.app",
        "http://localhost:8000"  # Für lokale Entwicklung
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📝 Notizen

- **Automatische Deployments**: Jeder Push zu `main` löst Deployment aus
- **Logs ansehen**: Railway Dashboard → Dein Projekt → Deployments → Logs
- **Kosten überwachen**: Railway Dashboard → Usage
- **Custom Domain**: Railway Settings → Domains → Add Custom Domain

---

## 🎯 Nächste Schritte

1. ✅ Repository auf GitHub pushen
2. ✅ Railway Projekt erstellen
3. ✅ Deployment abwarten (2-3 Minuten)
4. ✅ Terminal testen
5. 🎉 **Fertig! Dein Terminal läuft 24/7 in der Cloud!**

---

## 📞 Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- FastAPI Docs: https://fastapi.tiangolo.com

---

**Made with ⚡ by Atlas Terminal**
