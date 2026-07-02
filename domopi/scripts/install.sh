#!/usr/bin/env bash
# =============================================================================
# DomoPi – installation automatique sur Raspberry Pi OS Bookworm (Pi 5)
#
# Ce script :
#   1. installe les paquets systeme requis (Python 3.12 via apt, pigpio...) ;
#   2. cree un environnement virtuel et installe les dependances Python ;
#   3. genere le fichier .env s'il n'existe pas ;
#   4. installe et active les services systemd (domopi, pigpiod, matter-server).
#
# Usage : sudo bash scripts/install.sh
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-pi}"

echo "==> Installation de DomoPi dans ${PROJECT_DIR}"

# --- 1. Paquets systeme ------------------------------------------------------
echo "==> Paquets systeme"
apt-get update
apt-get install -y \
    python3 python3-venv python3-dev python3-pip \
    pigpio \
    libavahi-compat-libdnssd-dev \
    git curl

# Demon pigpio requis pour les timings Somfy RTS
systemctl enable --now pigpiod

# --- 2. Environnement Python -------------------------------------------------
echo "==> Environnement virtuel Python"
cd "${PROJECT_DIR}"
if [ ! -d .venv ]; then
    sudo -u "${SERVICE_USER}" python3 -m venv .venv
fi
sudo -u "${SERVICE_USER}" .venv/bin/pip install --upgrade pip
sudo -u "${SERVICE_USER}" .venv/bin/pip install -r requirements.txt

# --- 3. Configuration ---------------------------------------------------------
if [ ! -f .env ]; then
    echo "==> Generation du fichier .env"
    cp .env.example .env
    SECRET_KEY="$(.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')"
    sed -i "s|DOMOPI_SECRET_KEY=.*|DOMOPI_SECRET_KEY=${SECRET_KEY}|" .env
    sed -i "s|DOMOPI_ENVIRONMENT=.*|DOMOPI_ENVIRONMENT=production|" .env
    chown "${SERVICE_USER}:${SERVICE_USER}" .env
    chmod 600 .env
    echo "    -> Adapter .env (mot de passe admin, GPIO, pilote RF) avant le demarrage."
fi

mkdir -p data logs
chown -R "${SERVICE_USER}:${SERVICE_USER}" data logs

# --- 4. Services systemd -------------------------------------------------------
echo "==> Service systemd domopi"
sed -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" -e "s|__USER__|${SERVICE_USER}|g" \
    scripts/domopi.service > /etc/systemd/system/domopi.service

# Serveur Matter officiel (facultatif : commenter si non utilise)
echo "==> Service systemd matter-server"
sed -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" -e "s|__USER__|${SERVICE_USER}|g" \
    scripts/matter-server.service > /etc/systemd/system/matter-server.service

systemctl daemon-reload
systemctl enable --now matter-server || echo "    (matter-server non demarre : verifier l'installation)"
systemctl enable --now domopi

echo ""
echo "==> Installation terminee."
echo "    Interface Web : http://$(hostname -I | awk '{print $1}'):8000"
echo "    Documentation API : http://$(hostname -I | awk '{print $1}'):8000/api/docs"
echo "    Journaux : journalctl -u domopi -f"
