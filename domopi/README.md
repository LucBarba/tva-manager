# DomoPi 🏠

Système domotique complet et auto-hébergé pour **Raspberry Pi 5**, écrit
exclusivement en **Python 3.12** (compatible Raspberry Pi OS Bookworm).

- 🪟 **Volets roulants radio** — RF433 (codes appris) et **Somfy RTS** (rolling code)
- 💡 **Philips Hue** — découverte du pont, appairage, pièces, scènes, groupes, effets
- 🌡️ **Matter** — capteurs de température/humidité/batterie via le serveur officiel
- 🍎 **Apple Maison** — pont HomeKit exposant automatiquement tous les appareils
- 🖥️ **Interface Web moderne** — FastAPI + Bootstrap 5, temps réel (WebSocket),
  mode sombre, responsive
- 🔐 **Sécurité** — JWT, bcrypt, CSRF, CSP, validation Pydantic, HTTPS optionnel
- ⏰ **Programmations horaires**, groupes, journal d'événements, historique de mesures

---

## Sommaire

1. [Architecture](#architecture)
2. [Matériel requis](#matériel-requis)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Utilisation](#utilisation)
6. [API REST](#api-rest)
7. [Tests et qualité](#tests-et-qualité)
8. [Documentation détaillée](#documentation-détaillée)

---

## Architecture

```
domopi/
├── main.py                    # Point d'entrée (Uvicorn)
├── app/
│   ├── core/                  # Config (.env), logs rotatifs, sécurité, bus d'événements
│   ├── database/              # SQLite (SQLAlchemy 2.0) : modèles + sessions
│   ├── devices/
│   │   ├── base.py            # Contrat Device commun + registre central
│   │   ├── rf/                # Pilotes RF433 / Somfy RTS, apprentissage, volets
│   │   ├── hue/               # Client CLIP v2 + ampoules
│   │   └── matter/            # Client python-matter-server + capteurs
│   ├── homekit/               # Pont HAP (accessoires volet/lumière/capteur)
│   ├── scheduler/             # Programmations horaires (APScheduler)
│   ├── services/              # Logique métier (volets, Hue, Matter, users, historique)
│   ├── api/                   # API REST (schemas Pydantic, routes, auth JWT/CSRF)
│   ├── web/                   # Interface (Jinja2, Bootstrap 5, WebSocket)
│   └── utils/                 # Utilitaires transverses
├── tests/                     # Tests unitaires + intégration (pytest)
├── scripts/                   # install.sh + unités systemd
└── docs/                      # Architecture, installation, câblage
```

**Principes** : chaque intégration est isolée dans son module et expose ses
appareils via le contrat commun `Device` + le **registre central**. Les couches
hautes (API, HomeKit, planificateur) ne connaissent jamais le matériel : elles
parlent au registre et aux services. La synchronisation des états passe par un
**bus d'événements** (Observer) — l'interface Web (WebSocket) et Apple Maison
restent à jour en permanence. Changer d'émetteur radio = fournir un nouveau
pilote `RFDriver` (Factory + Strategy), sans toucher au métier.

## Matériel requis

| Usage | Matériel | GPIO par défaut |
|---|---|---|
| Émission RF433 | FS1000A ou équivalent 433,92 MHz | GPIO 17 |
| Réception RF433 (apprentissage) | RXB6 / XY-MK-5V | GPIO 27 |
| Somfy RTS | Émetteur **433,42 MHz** (quartz Somfy) | GPIO 17 |
| Hue | Pont Philips Hue sur le réseau local | — |
| Matter (Thread) | Dongle Thread/Border router ou appareils Wi-Fi | — |

## Installation

Sur un Raspberry Pi 5 sous Raspberry Pi OS Bookworm :

```bash
git clone <votre-depot> && cd domopi
sudo bash scripts/install.sh
```

Le script installe les paquets système (pigpio…), crée l'environnement
virtuel, génère `.env` avec une clé secrète aléatoire et installe les
services systemd (`domopi`, `matter-server`, `pigpiod`).

Installation manuelle (développement) :

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # adapter les valeurs
python main.py                # http://localhost:8000
```

Sans matériel radio, laisser `DOMOPI_RF_DRIVER=mock` : toutes les commandes
sont simulées et journalisées (un capteur Matter simulé est aussi exposé).

## Configuration

Toutes les valeurs sont dans `.env` (voir [.env.example](.env.example)) :
pilote RF et GPIO, pont Hue, serveur Matter, pont HomeKit (nom, port, code
PIN), base SQLite, journalisation (niveau, rotation), identifiants admin,
certificats HTTPS optionnels.

⚠️ En production : changer `DOMOPI_SECRET_KEY` et `DOMOPI_ADMIN_PASSWORD`.

## Utilisation

| Fonction | Où |
|---|---|
| Interface Web | `http://<ip-du-pi>:8000` |
| Documentation API (Swagger) | `http://<ip-du-pi>:8000/api/docs` |
| Appairage Apple Maison | app Maison → Ajouter un accessoire → code `031-45-154` (configurable) |
| Appairage Hue | Configuration → appuyer sur le bouton du pont → « Appairer » |
| Appairage Matter | Configuration → saisir le code d'appairage |
| Apprentissage RF433 | Volets → 📡 → choisir l'action → appuyer sur la télécommande |
| Appairage Somfy RTS | maintenir PROG sur la télécommande d'origine, puis Volets → 🔗 |
| Journaux | `journalctl -u domopi -f` et `logs/*.log` (rotation automatique) |

## API REST

Toutes les actions de l'interface passent par l'API (JWT Bearer ou cookie de
session + CSRF). Extrait :

```
POST /api/auth/login                        # connexion → JWT
GET  /api/devices                           # tous les appareils + états
POST /api/devices/{uid}/command             # commande générique
POST /api/shutters/{id}/open|close|stop     # volets
POST /api/shutters/groups/{id}/{action}     # groupes de volets
POST /api/hue/scenes/{id}/activate          # scènes Hue
POST /api/matter/commission                 # appairage Matter
GET  /api/history/events                    # journal
GET  /api/history/readings/{uid}            # historique température…
POST /api/schedules                         # programmation horaire
```

Documentation interactive complète : **`/api/docs`** (Swagger UI).

## Tests et qualité

```bash
.venv/bin/pytest                 # 48 tests unitaires + intégration
.venv/bin/ruff check app tests   # lint
.venv/bin/black app tests        # formatage
```

Le code applique : type hints partout, Pydantic v2 pour toute entrée,
docstrings sur chaque classe et fonction, architecture SOLID (abstractions
`Device`/`RFDriver`, injection de dépendances via le conteneur de services),
patterns Factory (pilotes RF), Observer (bus d'événements), Facade (services),
Adapter (accessoires HomeKit).

## Documentation détaillée

- [docs/architecture.md](docs/architecture.md) — conception, flux, schémas
- [docs/installation.md](docs/installation.md) — installation pas à pas, câblage, dépannage
