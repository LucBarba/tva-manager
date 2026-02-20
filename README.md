# TVA Manager Pro — PostgreSQL Edition

Application complète de gestion TVA pour auto-entrepreneurs et PME françaises.  
**Stack** : React 18 + Vite (frontend) · FastAPI + SQLAlchemy (backend) · PostgreSQL 16 (BDD)

---

## 🚀 Démarrage rapide (Docker — recommandé)

### Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et en cours d'exécution

### Lancement en une commande

```bash
docker compose up
```

Ouverture automatique :
| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:5173        |
| Backend    | http://localhost:8000        |
| API docs   | http://localhost:8000/docs   |
| PostgreSQL | localhost:5432               |

> Lors du premier lancement, Docker télécharge les images (~2 min).  
> Les données sont **persistées** dans un volume Docker nommé `tva_postgres_data`.

### Arrêter l'application

```bash
docker compose down          # arrête les conteneurs
docker compose down -v       # arrête ET supprime les données
```

---

## 🛠 Lancement sans Docker (développement)

### 1. PostgreSQL — démarrer une instance locale

**macOS (Homebrew)**
```bash
brew install postgresql@16
brew services start postgresql@16
createuser -s tva_user
createdb -O tva_user tva_db
psql -U tva_user -d tva_db -c "ALTER USER tva_user PASSWORD 'tva_pass';"
```

**Windows**
Téléchargez [PostgreSQL](https://www.postgresql.org/download/windows/) et créez l'utilisateur via pgAdmin.

**Linux (Ubuntu/Debian)**
```bash
sudo apt install postgresql
sudo -u postgres createuser -P tva_user    # mot de passe : tva_pass
sudo -u postgres createdb -O tva_user tva_db
```

### 2. Backend FastAPI

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Le backend crée automatiquement les tables `invoices` et `expenses` au démarrage.

### 3. Frontend React

```bash
cd frontend
npm install
npm run dev
```

Ouvre http://localhost:5173

---

## 🏗 Architecture

```
tva-postgres/
├── docker-compose.yml          ← Développement (hot-reload)
├── docker-compose.prod.yml     ← Production (nginx + build optimisé)
├── init.sql                    ← Script SQL initial (données de démo optionnelles)
│
├── backend/
│   ├── main.py                 ← FastAPI — toutes les routes CRUD + stats
│   ├── database.py             ← Connexion SQLAlchemy + session
│   ├── models.py               ← Modèles ORM (invoices, expenses)
│   ├── schemas.py              ← Schémas Pydantic (validation)
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    ├── src/
    │   ├── App.jsx             ← Application React complète
    │   ├── main.jsx
    │   └── index.css
    ├── index.html
    ├── vite.config.js          ← Proxy API → backend
    ├── package.json
    ├── Dockerfile              ← Build multi-stage (Node → nginx)
    └── nginx.conf
```

---

## 📡 API REST

| Méthode  | Endpoint                     | Description                    |
|----------|------------------------------|--------------------------------|
| GET      | `/api/invoices`              | Lister toutes les factures     |
| POST     | `/api/invoices`              | Créer une facture              |
| PUT      | `/api/invoices/{id}`         | Modifier une facture           |
| DELETE   | `/api/invoices/{id}`         | Supprimer une facture          |
| GET      | `/api/expenses`              | Lister toutes les dépenses     |
| POST     | `/api/expenses`              | Créer une dépense              |
| PUT      | `/api/expenses/{id}`         | Modifier une dépense           |
| DELETE   | `/api/expenses/{id}`         | Supprimer une dépense          |
| GET      | `/api/stats/dashboard`       | KPIs du tableau de bord        |
| GET      | `/api/stats/vat`             | Stats TVA mensuelles           |
| GET      | `/api/stats/revenue?year=N`  | CA par mois pour l'année N     |
| GET      | `/health`                    | État du serveur                |

Documentation interactive : **http://localhost:8000/docs**

---

## 🔧 Variables d'environnement

Copiez `.env.example` en `.env` pour surcharger les valeurs par défaut :

```bash
cp .env.example .env
```

| Variable       | Défaut                                            | Description              |
|----------------|---------------------------------------------------|--------------------------|
| DATABASE_URL   | postgresql://tva_user:tva_pass@postgres:5432/tva_db | URL de connexion PostgreSQL |
| VITE_API_URL   | http://localhost:8000                             | URL du backend (frontend)|

---

## 🗃 Données de démo

Pour insérer des données d'exemple, décommentez les `INSERT` dans `init.sql`.  
⚠️ Ce fichier n'est lu qu'à la **première création** de la base (volume vide).

Pour réinitialiser et relancer avec les données de démo :
```bash
docker compose down -v   # supprime le volume
# Décommentez les INSERT dans init.sql
docker compose up
```

---

## 📦 Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

Le frontend est buildé (Vite) et servi par nginx sur le port **80**.

