# 🚀 Atlas Terminal V1.1.1 - Setup Guide

## ⚡ Quick Start (5 Minuten)

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

**Was wird installiert:**
- FastAPI (Backend Framework)
- JWT Authentication (python-jose, passlib, bcrypt)
- Data Processing (pandas, numpy, yfinance)
- APIs (fredapi, requests)

### 2. Admin-User erstellen

```bash
python create_user.py
```

**Interaktives Menü:**
1. Wähle "1" für "Create new user"
2. Username: `admin`
3. Password: `<dein-sicheres-passwort>`
4. Full Name: `Admin User`
5. Email: `admin@atlas.com`
6. Admin user? `y`

✅ **Admin-User erstellt!**

### 3. Backend starten

```bash
python backend.py
```

Du solltest sehen:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 4. Terminal öffnen

Öffne im Browser:
```
http://127.0.0.1:8000/login.html
```

Login mit deinen Admin-Credentials!

---

## 📦 Was ist neu in v1.1.1?

### ✨ Features

1. **User Authentication System**
   - JWT-basierte sichere Login
   - Password Hashing mit bcrypt
   - Admin & Normal User Rollen

2. **User-spezifische Watchlists**
   - Eigene Asset-Listen pro User
   - Einfaches Hinzufügen/Entfernen

3. **Konfigurierbare Dashboards**
   - Flexible Widget-Positionierung
   - Verschiedene Widget-Typen (Risk Radar, News, Charts)
   - Speicherung der Konfiguration

4. **Profile Management**
   - User-Einstellungen
   - Theme, Language, Notifications

5. **Admin-Backend**
   - User erstellen/löschen
   - Überblick über alle User
   - CLI-Tool für User-Management

---

## 🗂️ Dateistruktur

```
Atlas Terminal V1.1.1/
├── backend.py              # FastAPI Backend + API Endpoints
├── auth.py                 # Authentication Module (JWT, Password Hashing)
├── create_user.py          # CLI Tool für User-Verwaltung
├── login.html              # Login-Seite
├── terminal.html           # Haupt-Terminal (Dashboard, Analyzer, etc.)
├── index.html              # Landing Page
├── atlas_users.db          # SQLite Database (automatisch erstellt)
├── requirements.txt        # Python Dependencies
├── USER_MANAGEMENT.md      # Vollständige User-Management Docs
├── SETUP.md                # Dieses Dokument
└── RAILWAY_DEPLOYMENT.md   # Cloud Deployment Guide
```

---

## 🔧 Detaillierte Installation

### Schritt 1: Python Environment

**Empfohlen: Virtual Environment**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Schritt 2: Dependencies

```bash
pip install -r requirements.txt
```

**Wichtige Packages:**
- `python-jose[cryptography]` - JWT Tokens
- `passlib[bcrypt]` - Password Hashing
- `bcrypt` - Crypto Backend
- `fastapi` - Web Framework
- `uvicorn` - ASGI Server
- `yfinance` - Market Data
- `fredapi` - Economic Data (Risk Radar)

### Schritt 3: Database Setup

Die Datenbank wird **automatisch** beim ersten Start erstellt!

```python
# In auth.py wird init_database() automatisch aufgerufen
init_database()  # Erstellt atlas_users.db mit allen Tabellen
```

**Tabellen:**
- `users` - User-Daten
- `watchlist` - Asset-Watchlists
- `user_widgets` - Dashboard-Konfiguration

### Schritt 4: Ersten User erstellen

**Option A: Interaktiv**
```bash
python create_user.py
```

**Option B: Direkt**
```bash
python create_user.py create admin MeinPasswort123 --admin --email admin@test.com
```

**Option C: Python Console**
```python
from auth import create_user, UserCreate

user = create_user(UserCreate(
    username="admin",
    password="MeinPasswort123",
    email="admin@test.com",
    full_name="Admin User",
    is_admin=True
))
print(f"User created: {user.username}")
```

### Schritt 5: Backend starten

```bash
python backend.py
```

**Oder mit Uvicorn direkt:**
```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

**Server läuft auf:**
- Backend API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- Login: http://127.0.0.1:8000/login.html
- Terminal: http://127.0.0.1:8000/terminal.html

---

## 👥 Beta-Kunden Setup

### Szenario: 5 Beta-User erstellen

**Batch-Script erstellen: `create_beta_users.py`**

```python
from auth import create_user, UserCreate

beta_users = [
    {"username": "beta1", "password": "BetaPass123!", "email": "beta1@test.com", "name": "Beta User 1"},
    {"username": "beta2", "password": "BetaPass456!", "email": "beta2@test.com", "name": "Beta User 2"},
    {"username": "beta3", "password": "BetaPass789!", "email": "beta3@test.com", "name": "Beta User 3"},
    {"username": "beta4", "password": "BetaPass012!", "email": "beta4@test.com", "name": "Beta User 4"},
    {"username": "beta5", "password": "BetaPass345!", "email": "beta5@test.com", "name": "Beta User 5"},
]

for user_data in beta_users:
    try:
        user = create_user(UserCreate(
            username=user_data["username"],
            password=user_data["password"],
            email=user_data["email"],
            full_name=user_data["name"],
            is_admin=False
        ))
        print(f"✓ Created: {user.username}")
    except Exception as e:
        print(f"✗ Failed: {user_data['username']} - {e}")

print("\n✅ All beta users created!")
```

**Ausführen:**
```bash
python create_beta_users.py
```

**Credentials ausgeben:**
```bash
python create_user.py list
```

---

## 🌐 Production Deployment (Railway)

### Quick Deployment

1. **Push zu GitHub**
   ```bash
   git init
   git add .
   git commit -m "Atlas Terminal v1.1.1 with Authentication"
   git remote add origin https://github.com/USERNAME/atlas-terminal.git
   git push -u origin main
   ```

2. **Railway Connect**
   - Gehe zu https://railway.app
   - "New Project" → "Deploy from GitHub"
   - Repository auswählen
   - Deploy!

3. **Admin-User auf Railway erstellen**

   **Option A: Railway Shell**
   - Railway Dashboard → Shell
   - `python create_user.py create admin Pass123 --admin`

   **Option B: Lokal + SQLite Upload**
   - Lokal User erstellen
   - `atlas_users.db` zu Railway hochladen

### Environment Variables (Optional)

Für Production empfohlen:

```env
SECRET_KEY=<generiere-sicheren-32-byte-key>
NEWS_API_KEY=<dein-newsapi-key>
FRED_API_KEY=<dein-fred-api-key>
```

**Generiere sicheren SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
# Ausgabe: z.B. "xPq9vN2mK4jL8oT5hR3fG6wE1cY7bA0"
```

---

## 🧪 Testing

### 1. API Tests

**Login Test:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Pass123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Get Current User:**
```bash
TOKEN="<dein-token-hier>"

curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Frontend Tests

1. Öffne http://127.0.0.1:8000/login.html
2. Login mit Admin-Credentials
3. Prüfe Redirect zu terminal.html
4. Teste alle Features:
   - Dashboard
   - Analyzer
   - Markets
   - News
   - Risk Radar
   - Profile

### 3. Database Tests

```bash
# SQLite Console
sqlite3 atlas_users.db

# Queries
SELECT * FROM users;
SELECT * FROM watchlist;
SELECT * FROM user_widgets;

.exit
```

---

## ⚙️ Konfiguration

### Backend (backend.py)

**Port ändern:**
```python
# Zeile 1523
port = int(os.environ.get("PORT", 8080))  # Standard: 8000
```

**CORS anpassen:**
```python
# Zeile 36-42
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Statt "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Authentication (auth.py)

**Token-Gültigkeit ändern:**
```python
# Zeile 18
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 Tage statt 24h
```

**SECRET_KEY setzen:**
```python
# Zeile 17
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-key-nur-für-dev")
```

---

## 🐛 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'jose'`

**Lösung:**
```bash
pip install python-jose[cryptography]
```

### Problem: `ModuleNotFoundError: No module named 'passlib'`

**Lösung:**
```bash
pip install passlib[bcrypt]
```

### Problem: Port 8000 bereits in Verwendung

**Lösung:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Problem: Database locked

**Lösung:**
```bash
# Windows
del atlas_users.db-journal

# Linux/Mac
rm atlas_users.db-journal
```

### Problem: Login funktioniert nicht

**Checklist:**
1. Backend läuft? → `python backend.py`
2. User existiert? → `python create_user.py list`
3. Password korrekt?
4. Browser Console prüfen (F12)
5. Backend Logs prüfen

---

## 📚 Weitere Dokumentation

- **USER_MANAGEMENT.md** - Vollständige User-Management Docs
- **RAILWAY_DEPLOYMENT.md** - Cloud Deployment
- **RISK_RADAR_README.md** - Risk Radar Feature
- **API Docs** - http://127.0.0.1:8000/docs (automatisch generiert)

---

## 🎯 Next Steps

Nach dem Setup:

1. ✅ Login testen
2. ✅ Watchlist hinzufügen
3. ✅ Dashboard anpassen
4. ✅ Beta-User erstellen
5. ✅ Auf Railway deployen

---

## 💡 Tips

### Performance

- **SQLite** ist ideal für <100 Users
- Für mehr: PostgreSQL empfohlen
- Railway bietet PostgreSQL Plugin

### Sicherheit

- **Nie** SECRET_KEY im Code hardcoden
- **Immer** HTTPS in Production
- **Regelmäßig** Backups von `atlas_users.db`

### Monitoring

```python
# User Activity Dashboard
import sqlite3

conn = sqlite3.connect('atlas_users.db')
cursor = conn.cursor()

# Aktive User (letzte 7 Tage)
cursor.execute("""
    SELECT username, last_login
    FROM users
    WHERE last_login > datetime('now', '-7 days')
    ORDER BY last_login DESC
""")

for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")
```

---

## ✅ Checkliste

- [ ] Python 3.8+ installiert
- [ ] Requirements installiert (`pip install -r requirements.txt`)
- [ ] Admin-User erstellt
- [ ] Backend läuft (Port 8000)
- [ ] Login funktioniert
- [ ] Terminal lädt
- [ ] Alle Features getestet
- [ ] Beta-User erstellt
- [ ] Credentials verschickt
- [ ] Railway Deployment (optional)

---

**🎉 Fertig! Viel Erfolg mit dem Atlas Terminal!**

Support: [USER_MANAGEMENT.md](USER_MANAGEMENT.md)

Made with ⚡ by Atlas Terminal
