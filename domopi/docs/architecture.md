# Architecture de DomoPi

## Vue d'ensemble

```
                          ┌───────────────────────────────┐
                          │        Interface Web          │
                          │  (Bootstrap 5, WebSocket)     │
                          └──────────────┬────────────────┘
                                         │ HTTPS / WS
┌──────────────┐          ┌──────────────▼────────────────┐
│ Apple Maison │◄────────►│         FastAPI               │
│  (HomeKit)   │   HAP    │  API REST /api (Swagger)      │
└──────┬───────┘          └──────────────┬────────────────┘
       │                                 │
┌──────▼─────────────────────────────────▼────────────────┐
│                  Conteneur de services                   │
│  ShutterService · HueService · MatterService ·           │
│  SchedulerService · UserService · HistoryService         │
└──────┬───────────────┬───────────────┬──────────────────┘
       │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────────────────┐
│  Bus         │ │  Registre   │ │  SQLite (SQLAlchemy)    │
│ d'événements │ │  Device     │ │  users · shutters ·     │
│ (pub/sub)    │ │  (registry) │ │  schedules · logs …     │
└──────────────┘ └──────┬──────┘ └─────────────────────────┘
                        │
        ┌───────────────┼─────────────────┐
┌───────▼──────┐ ┌──────▼──────┐ ┌────────▼─────────┐
│ RFDriver     │ │ HueClient   │ │ MatterController │
│ rf433 /      │ │ (CLIP v2)   │ │ (matter-server)  │
│ somfy_rts /  │ │             │ │                  │
│ mock         │ │             │ │                  │
└───────┬──────┘ └──────┬──────┘ └────────┬─────────┘
        │               │                 │
   GPIO 433 MHz     Pont Hue        Serveur Matter
```

## Couches et responsabilités

| Couche | Rôle | Ne connaît pas |
|---|---|---|
| `app/devices/*` (pilotes) | Parler au matériel (GPIO, HTTP, WS) | la base, l'API |
| `app/devices/base.py` | Contrat `Device` + `DeviceRegistry` | les pilotes concrets |
| `app/services/*` | Orchestration métier, persistance, événements | HTTP, HomeKit |
| `app/api/*` | Validation Pydantic, auth, mapping HTTP | le matériel |
| `app/homekit/*` | Adapter `Device` → accessoires HAP | les pilotes |
| `app/web/*` | Rendu HTML, statiques, WebSocket | le métier (passe par l'API) |

## Flux principaux

### Commande d'un volet (interface → moteur)

1. Le navigateur appelle `POST /api/shutters/{id}/close` (JWT + CSRF).
2. La route délègue à `ShutterService.send_command`.
3. Le service ouvre une transaction : lit le protocole, incrémente le
   rolling code (Somfy) ou charge le code appris (RF433), met à jour la
   position estimée.
4. L'émission radio s'exécute dans un thread (`asyncio.to_thread`) sous un
   verrou global — un seul émetteur physique.
5. Un événement `DEVICE_STATE_CHANGED` est publié sur le bus.
6. Abonnés : le WebSocket pousse le nouvel état aux navigateurs, le pont
   HomeKit met à jour Apple Maison, l'historique journalise l'action.

### Synchronisation HomeKit

Le pont HAP tourne dans un thread dédié (HAP-python possède sa propre
boucle). Les commandes venant d'Apple Maison sont renvoyées vers la boucle
asyncio principale par `asyncio.run_coroutine_threadsafe` ; les changements
d'état suivent le chemin inverse via le bus d'événements.

### Protocole Somfy RTS

`build_somfy_frame()` (fonction pure, testée unitairement) construit la
trame de 7 octets : clé, bouton, rolling code 16 bits, adresse 24 bits,
checksum XOR sur les quartets, obfuscation octet à octet. L'émission
utilise les **ondes pigpio** pour garantir les timings (symbole 640 µs,
synchronisations matérielle/logicielle, réveil 9,4 ms). Le rolling code est
incrémenté en base **avant** l'émission : une trame perdue ne désynchronise
pas le moteur (les moteurs tolèrent une large fenêtre de codes).

## Design patterns employés

- **Factory** — `create_rf_driver()` instancie le pilote configuré.
- **Strategy** — `RFDriver` interchangeable (rf433 / somfy_rts / mock).
- **Observer** — `EventBus` découple producteurs et consommateurs d'états.
- **Facade** — chaque service expose une API métier simple.
- **Adapter** — accessoires HomeKit adaptant `Device` au protocole HAP.
- **Registry** — annuaire central des périphériques.
- **Dependency Injection** — conteneur de services + `Depends` FastAPI.

## Sécurité

- Mots de passe **bcrypt** (sel automatique).
- **JWT** signés HS256, jetons d'accès (60 min) et de rafraîchissement (7 j),
  le type de jeton est vérifié au décodage.
- Interface Web : cookie **HttpOnly** + **CSRF double soumission signée**
  (HMAC-SHA256) exigée sur toute mutation authentifiée par cookie.
- **CSP**, `X-Frame-Options`, `X-Content-Type-Options` sur chaque réponse ;
  échappement Jinja2 + `esc()` côté client contre le XSS.
- Validation **Pydantic** de toutes les entrées (bornes, formats, longueurs).
- Rôles `admin`/`user` ; le dernier administrateur ne peut pas être supprimé.
- HTTPS optionnel (certificat/clé dans `.env`).

## Base de données

SQLite en mode WAL, clés étrangères actives. Tables : `users`, `shutters`
(codes RF JSON, adresse/rolling code Somfy), `shutter_groups` (+ table
d'association), `schedules`, `event_logs`, `sensor_readings`, `settings`
(clé d'application Hue…).

## Extensibilité

Ajouter un type d'appareil = créer un module sous `app/devices/`, implémenter
`Device`, l'enregistrer dans le registre depuis un service, et (optionnel)
fournir un accessoire HomeKit. Rien d'autre à modifier : l'API générique
`/api/devices` et le WebSocket le prennent en charge automatiquement.
