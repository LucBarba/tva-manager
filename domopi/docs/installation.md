# Installation détaillée

## 1. Prérequis

- Raspberry Pi 5, Raspberry Pi OS **Bookworm** (64 bits), Python 3.12
- Accès réseau local (pont Hue, appareils Matter, HomeKit/mDNS)
- Matériel radio selon vos volets (voir tableau du README)

## 2. Câblage radio

### Émetteur 433 MHz (FS1000A ou émetteur 433,42 MHz pour Somfy)

| Broche module | Raspberry Pi |
|---|---|
| VCC | 5 V (broche 2) |
| GND | GND (broche 6) |
| DATA | GPIO 17 (broche 11) |

### Récepteur 433 MHz (apprentissage RF433)

| Broche module | Raspberry Pi |
|---|---|
| VCC | 5 V (broche 4) |
| GND | GND (broche 9) |
| DATA | GPIO 27 (broche 13) |

> ⚠️ **Somfy RTS émet sur 433,42 MHz** : un FS1000A standard (433,92 MHz)
> a une portée très réduite. Remplacer le quartz ou utiliser un émetteur
> prévu pour cette fréquence. Une antenne de 17,3 cm améliore nettement la
> portée.

## 3. Installation automatique

```bash
sudo bash scripts/install.sh
```

Le script :
1. installe `python3-venv`, `pigpio`, les en-têtes mDNS ;
2. active `pigpiod` (requis pour les timings Somfy) ;
3. crée `.venv` et installe `requirements.txt` ;
4. génère `.env` (clé secrète aléatoire, droits 600) ;
5. installe et démarre les services `domopi` et `matter-server`.

## 4. Configuration `.env`

Champs à vérifier avant le premier démarrage :

```ini
DOMOPI_ADMIN_PASSWORD=...      # mot de passe du compte admin initial
DOMOPI_RF_DRIVER=somfy_rts     # ou rf433, ou mock (sans matériel)
DOMOPI_RF_TX_GPIO=17
DOMOPI_RF_RX_GPIO=27
DOMOPI_HOMEKIT_PINCODE=031-45-154
```

Pour HTTPS, fournir un certificat (par exemple généré par `mkcert` ou un
reverse proxy interne) :

```ini
DOMOPI_SSL_CERTFILE=/etc/ssl/domopi/cert.pem
DOMOPI_SSL_KEYFILE=/etc/ssl/domopi/key.pem
```

## 5. Premier démarrage

```bash
sudo systemctl status domopi        # doit être « active (running) »
journalctl -u domopi -f             # suivi des journaux
```

Ouvrir `http://<ip-du-pi>:8000`, se connecter avec le compte admin, puis :

1. **Hue** : Configuration → bouton du pont → « Appairer le pont ».
2. **Matter** : Configuration → code d'appairage de l'appareil.
3. **Volets Somfy** : créer le volet (protocole Somfy RTS), maintenir le
   bouton PROG de la télécommande d'origine jusqu'au va-et-vient du volet,
   puis cliquer sur 🔗 (PROG) dans la minute.
4. **Volets RF433** : créer le volet (protocole RF433), puis 📡 pour
   apprendre chaque bouton de la télécommande.
5. **Apple Maison** : app Maison → « + » → Ajouter un accessoire →
   « Autres options » → DomoPi Bridge → saisir le code PIN.

## 6. Mise à jour

```bash
cd domopi && git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart domopi
```

## 7. Dépannage

| Symptôme | Piste |
|---|---|
| `Demon pigpiod injoignable` | `sudo systemctl start pigpiod` |
| Volet Somfy ne réagit plus | rolling code désynchronisé : refaire l'appairage PROG |
| Pont Hue introuvable | renseigner `DOMOPI_HUE_BRIDGE_IP` dans `.env` |
| Matter indisponible | `sudo systemctl status matter-server` |
| HomeKit « accessoire non trouvé » | vérifier que le Pi et l'iPhone sont sur le même VLAN (mDNS) ; supprimer `data/homekit.state` pour ré-appairer |
| Codes RF433 non captés | vérifier l'alimentation 5 V du récepteur et l'antenne |

Les journaux par module sont dans `logs/` (`rf.log`, `hue.log`,
`matter.log`, `homekit.log`, `web.log`, `scheduler.log`) avec rotation
automatique (5 × 5 Mo).
