# 👤 Atlas Terminal - User Management Guide

## 📋 Übersicht

Atlas Terminal v1.1.1 verfügt jetzt über ein vollständiges User Authentication System mit:

- ✅ JWT-basierte Authentication
- ✅ Sichere Password-Speicherung (bcrypt)
- ✅ Admin-Backend für User-Verwaltung
- ✅ User-spezifische Watchlists
- ✅ Konfigurierbare Dashboard-Widgets
- ✅ Profile-Verwaltung

---

## 🚀 Quick Start

### 1. Dependencies installieren

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### 2. Ersten Admin-User erstellen

```bash
# Interaktiver Modus
python create_user.py

# Oder direkt:
python create_user.py create admin MeinSicheresPasswort123 --admin --email admin@atlas.com --name "Admin User"
```

### 3. Backend starten

```bash
python backend.py
```

### 4. Terminal öffnen

Öffne im Browser:
- http://127.0.0.1:8000/login.html

Login mit deinen Credentials!

---

## 🔧 User-Verwaltung

### CLI Tool: `create_user.py`

#### Interaktiver Modus

```bash
python create_user.py
```

**Menü:**
```
1. Create new user
2. List all users
3. Exit
```

#### Non-Interactive Mode

**User erstellen:**
```bash
python create_user.py create <username> <password> [options]

Options:
  --admin              Make user an admin
  --email <email>      Set email address
  --name <name>        Set full name
```

**Beispiele:**
```bash
# Admin User
python create_user.py create admin Pass123 --admin --email admin@atlas.com

# Beta User
python create_user.py create betauser1 Test456 --email user1@test.com --name "Beta User 1"

# Normaler User
python create_user.py create trader Pass789
```

**Alle User auflisten:**
```bash
python create_user.py list
```

---

## 🔐 API Endpoints

### Authentication

#### POST `/api/auth/login`
Login und JWT Token erhalten

**Request:**
```json
{
  "username": "admin",
  "password": "Pass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### GET `/api/auth/me`
Aktuellen User abrufen (benötigt Token)

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "username": "admin",
  "email": "admin@atlas.com",
  "full_name": "Admin User",
  "disabled": false,
  "is_admin": true
}
```

### Admin Endpoints (nur für Admins)

#### POST `/api/auth/register`
Neuen User erstellen

**Headers:**
```
Authorization: Bearer <admin-token>
```

**Request:**
```json
{
  "username": "newuser",
  "password": "SecurePass123",
  "email": "new@example.com",
  "full_name": "New User",
  "is_admin": false
}
```

#### GET `/api/admin/users`
Alle User auflisten

#### DELETE `/api/admin/users/{username}`
User löschen

---

## 📊 User Features

### Watchlist

**GET `/api/user/watchlist`**
User's Watchlist abrufen

**POST `/api/user/watchlist`**
Asset zur Watchlist hinzufügen

**Request:**
```json
{
  "symbol": "AAPL",
  "category": "Aktien"
}
```

**DELETE `/api/user/watchlist/{symbol}`**
Asset von Watchlist entfernen

### Dashboard Widgets

**GET `/api/user/widgets`**
User's Dashboard-Widgets abrufen

**POST `/api/user/widgets`**
Neues Widget hinzufügen

**Request:**
```json
{
  "widget_type": "risk_radar",
  "widget_config": {
    "refresh_interval": 300
  },
  "position_x": 50,
  "position_y": 50,
  "width": 600,
  "height": 400
}
```

**PUT `/api/user/widgets/{widget_id}`**
Widget aktualisieren

**DELETE `/api/user/widgets/{widget_id}`**
Widget löschen

### User Settings

**GET `/api/user/settings`**
User-Einstellungen abrufen

**POST `/api/user/settings`**
Einstellungen speichern

**Request:**
```json
{
  "theme": "dark",
  "language": "de",
  "notifications": true,
  "default_timeframe": "1d"
}
```

---

## 💾 Datenbank

### SQLite Database: `atlas_users.db`

**Tabellen:**

#### `users`
```sql
id              INTEGER PRIMARY KEY
username        TEXT UNIQUE NOT NULL
hashed_password TEXT NOT NULL
email           TEXT
full_name       TEXT
disabled        INTEGER DEFAULT 0
is_admin        INTEGER DEFAULT 0
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
last_login      TIMESTAMP
user_settings   TEXT (JSON)
```

#### `watchlist`
```sql
id          INTEGER PRIMARY KEY
username    TEXT NOT NULL
symbol      TEXT NOT NULL
category    TEXT
added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
FOREIGN KEY (username) REFERENCES users(username)
```

#### `user_widgets`
```sql
id            INTEGER PRIMARY KEY
username      TEXT NOT NULL
widget_type   TEXT NOT NULL
widget_config TEXT (JSON)
position_x    INTEGER
position_y    INTEGER
width         INTEGER
height        INTEGER
created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
FOREIGN KEY (username) REFERENCES users(username)
```

---

## 🎯 Beta-Kunden Workflow

### Schritt 1: User erstellen

```bash
# Erstelle 5 Beta-User
python create_user.py create beta_user_1 BetaPass123! --email beta1@test.com --name "Beta User 1"
python create_user.py create beta_user_2 BetaPass456! --email beta2@test.com --name "Beta User 2"
python create_user.py create beta_user_3 BetaPass789! --email beta3@test.com --name "Beta User 3"
python create_user.py create beta_user_4 BetaPass012! --email beta4@test.com --name "Beta User 4"
python create_user.py create beta_user_5 BetaPass345! --email beta5@test.com --name "Beta User 5"
```

### Schritt 2: Credentials versenden

**Email-Template:**

```
Hallo [Name],

Willkommen im Atlas Terminal Beta-Programm!

Deine Login-Daten:
URL: https://deine-railway-url.up.railway.app/login.html
Username: beta_user_1
Password: BetaPass123!

Features:
✅ Probability Analyzer
✅ Live Market Data
✅ Risk Radar
✅ Financial News
✅ Personalisiertes Dashboard
✅ Custom Watchlists

Support: support@atlas-terminal.com

Viel Erfolg!
Atlas Terminal Team
```

### Schritt 3: User überwachen

```bash
# Alle User auflisten
python create_user.py list
```

**Oder über API:**
```bash
curl -X GET "http://localhost:8000/api/admin/users" \
  -H "Authorization: Bearer <admin-token>"
```

### Schritt 4: User bei Bedarf löschen

```bash
curl -X DELETE "http://localhost:8000/api/admin/users/beta_user_1" \
  -H "Authorization: Bearer <admin-token>"
```

---

## 🔒 Sicherheit

### Password Requirements
- Mindestens 6 Zeichen (für Production: 8+ empfohlen)
- Automatisches bcrypt-Hashing
- Niemals im Klartext gespeichert

### JWT Tokens
- Gültigkeit: 24 Stunden
- Sichere Secret Key (automatisch generiert)
- Bearer Authentication

### Environment Variables

Für Production empfohlen:

```bash
# .env oder Railway Environment Variables
SECRET_KEY=dein-super-sicherer-secret-key-hier
NEWS_API_KEY=dein-news-api-key
FRED_API_KEY=dein-fred-api-key
```

**In backend.py wird automatisch gelesen:**
```python
SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
```

---

## 🚀 Railway Deployment

### Zusätzliche Schritte für User-System:

1. **Database Persistence**
   Railway speichert SQLite automatisch im Volume

2. **Environment Variables setzen**
   ```
   SECRET_KEY=<generiere-einen-sicheren-key>
   ```

3. **Ersten Admin-User erstellen**
   ```bash
   # Nach Deployment über Railway CLI:
   railway run python create_user.py create admin <password> --admin
   ```

   **Oder direkt im Container:**
   - Railway Dashboard → Shell
   - `python create_user.py create admin Pass123 --admin`

---

## 📝 Frontend Integration

### Login-Flow

1. User öffnet `/login.html`
2. Login → JWT Token im `localStorage` gespeichert
3. Redirect zu `/terminal.html`
4. Terminal prüft Token bei jedem API-Call
5. Bei Fehler → Redirect zu `/login.html`

### Token Storage

```javascript
// Token speichern
localStorage.setItem('atlasToken', token);

// Token abrufen
const token = localStorage.getItem('atlasToken');

// API Call mit Token
fetch(`${API_URL}/api/user/watchlist`, {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});

// Logout
localStorage.removeItem('atlasToken');
window.location.href = '/login.html';
```

---

## 🐛 Troubleshooting

### Problem: "Could not validate credentials"
**Lösung:** Token abgelaufen oder ungültig. Neu einloggen.

### Problem: "Not enough permissions"
**Lösung:** Endpoint benötigt Admin-Rechte. User ist kein Admin.

### Problem: "Username already exists"
**Lösung:** Username bereits vergeben. Anderen wählen.

### Problem: Database locked
**Lösung:**
```bash
# Windows
del atlas_users.db-journal

# Linux/Mac
rm atlas_users.db-journal
```

### Problem: Forgot admin password
**Lösung:**
```python
# Python-Console oder Script
import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_password_hash = pwd_context.hash("NeuesPasswort123")

conn = sqlite3.connect("atlas_users.db")
cursor = conn.cursor()
cursor.execute("UPDATE users SET hashed_password = ? WHERE username = ?",
               (new_password_hash, "admin"))
conn.commit()
conn.close()
```

---

## 📊 Monitoring

### User Activity

```sql
-- Letzte Logins
SELECT username, last_login
FROM users
ORDER BY last_login DESC;

-- Anzahl Watchlist-Items pro User
SELECT username, COUNT(*) as items
FROM watchlist
GROUP BY username;

-- User mit meisten Widgets
SELECT username, COUNT(*) as widgets
FROM user_widgets
GROUP BY username
ORDER BY widgets DESC;
```

---

## 🎉 Fertig!

Dein Atlas Terminal ist jetzt bereit für Beta-Kunden!

**Next Steps:**
1. ✅ Admin-User erstellen
2. ✅ Beta-User erstellen
3. ✅ Credentials versenden
4. ✅ Feedback sammeln
5. 🚀 Live gehen!

---

**Made with ⚡ by Atlas Terminal**
