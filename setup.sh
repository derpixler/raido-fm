#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# RAIDO FM — Hetzner CX23 Setup Script
# =============================================================================
# Läuft auf: Ubuntu 24.04 LTS, 2 vCPU, 4 GB RAM, 40 GB SSD
# Domain: raido.live (A-Record + Wildcard CNAME auf Server-IP)
#
# Usage:  curl -fsSL https://.../setup.sh | bash           (schnell, root)
#   oder: chmod +x setup.sh && sudo ./setup.sh               (manuell)
# =============================================================================

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[x]${NC} $*"; exit 1; }

# ── Config (anpassbar via Umgebungsvariablen oder interaktiv) ──────────────
DOMAIN="${DOMAIN:-raido.live}"
ACME_EMAIL="${ACME_EMAIL:-admin@raido.live}"
GIT_REPO="${GIT_REPO:-https://github.com/derpixler/raido-fm.git}"
APP_DIR="${APP_DIR:-/opt/raido-fm}"
HUB_PORT="${HUB_PORT:-3099}"
ADMIN_TOKEN="${ADMIN_TOKEN:-}"
LLM_DJ_BASE_URL="${LLM_DJ_BASE_URL:-https://api.deepseek.com}"
LLM_DJ_MODEL="${LLM_DJ_MODEL:-deepseek-chat}"
LLM_DJ_API_KEY="${LLM_DJ_API_KEY:-}"
LLM_FILTER_BASE_URL="${LLM_FILTER_BASE_URL:-https://api.deepseek.com}"
LLM_FILTER_MODEL="${LLM_FILTER_MODEL:-deepseek-chat}"
LLM_FILTER_API_KEY="${LLM_FILTER_API_KEY:-}"

# ── Root-Check ─────────────────────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] || err "Bitte als root ausfuehren: sudo ./setup.sh"

log "RAIDO FM — Hetzner CX23 Setup"
log "================================================"
log "Domain:    ${DOMAIN}"
log "Verzeichnis: ${APP_DIR}"
log ""

# =============================================================================
# 1. System-Pakete installieren
# =============================================================================
log "1/7 System-Pakete installieren..."

apt-get update -qq
apt-get install -y -qq curl git ufw nginx 2>&1 | tail -1

# Docker (offizielles Repo)
if ! command -v docker &>/dev/null; then
    log "Docker wird installiert..."
    curl -fsSL https://get.docker.com | sh
fi

log "System-Pakete: OK (docker $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ','))"

# =============================================================================
# 2. Firewall
# =============================================================================
log "2/7 Firewall konfigurieren..."

ufw --force reset >/dev/null 2>&1
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow ssh >/dev/null
ufw allow http >/dev/null
ufw allow https >/dev/null
ufw --force enable >/dev/null

log "UFW: nur SSH, HTTP, HTTPS offen"

# =============================================================================
# 3. Repository klonen
# =============================================================================
log "3/7 Repository klonen..."

if [[ -d "${APP_DIR}" ]]; then
    log "Verzeichnis existiert, pull..."
    git -C "${APP_DIR}" pull --ff-only
else
    git clone "${GIT_REPO}" "${APP_DIR}"
fi

cd "${APP_DIR}"

# =============================================================================
# 4. Environment konfigurieren
# =============================================================================
log "4/7 .env konfigurieren..."

if [[ ! -f .env ]]; then
    if [[ -z "${ADMIN_TOKEN}" ]]; then
        ADMIN_TOKEN=$(openssl rand -hex 32)
        log "Admin-Token generiert: ${ADMIN_TOKEN}"
    fi

    if [[ -z "${LLM_DJ_API_KEY}" ]]; then
        warn "LLM_DJ_API_KEY nicht gesetzt!"
        read -rp "DJ LLM API Key (DeepSeek/Groq): " LLM_DJ_API_KEY
    fi

    if [[ -z "${LLM_FILTER_API_KEY}" ]]; then
        warn "LLM_FILTER_API_KEY nicht gesetzt! (Enter fuer gleichen Key wie DJ)"
        read -rp "Filter LLM API Key: " LLM_FILTER_API_KEY
        [[ -z "${LLM_FILTER_API_KEY}" ]] && LLM_FILTER_API_KEY="${LLM_DJ_API_KEY}"
    fi

    cat > .env <<ENVEOF
# === RAIDO Hub + Station Config ===
HUB_PORT=${HUB_PORT}
TIME_SCALE=60
MAX_INPUT_CHARS=500
ADMIN_TOKEN=${ADMIN_TOKEN}

# === DJ LLM ===
LLM_DJ_BASE_URL=${LLM_DJ_BASE_URL}
LLM_DJ_MODEL=${LLM_DJ_MODEL}
LLM_DJ_API_KEY=${LLM_DJ_API_KEY}

# === Filter LLM ===
LLM_FILTER_BASE_URL=${LLM_FILTER_BASE_URL}
LLM_FILTER_MODEL=${LLM_FILTER_MODEL}
LLM_FILTER_API_KEY=${LLM_FILTER_API_KEY}
ENVEOF

    chmod 600 .env
    log ".env erstellt"
else
    log ".env existiert bereits — ueberspringe"
fi

# =============================================================================
# 5. NGINX Reverse Proxy (ersetzt geplantes Traefik, simpler)
# =============================================================================
log "5/7 NGINX Reverse Proxy konfigurieren..."

cat > /etc/nginx/sites-available/raido <<NGINXEOF
# RAIDO FM — NGINX Reverse Proxy
# Hub lauscht intern auf 127.0.0.1:${HUB_PORT}

server {
    listen 80;
    server_name ${DOMAIN} *.${DOMAIN};

    # Let's Encrypt HTTP-Challenge (fuer Certbot spaeter)
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:${HUB_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # SSE-Streaming (fuer /s/{slug}/sse)
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 24h;
        chunked_transfer_encoding on;
    }
}
NGINXEOF

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/raido /etc/nginx/sites-enabled/raido
nginx -t 2>&1 | tail -1
systemctl enable nginx --now
systemctl reload nginx 2>&1 | tail -1

log "NGINX: konfiguriert, lauscht auf :80 → Hub :${HUB_PORT}"

# =============================================================================
# 6. Docker Compose: Bauen & Starten
# =============================================================================
log "6/7 Docker Compose: Build & Start..."

# Station-Image vorab bauen (damit Hub es beim Station-Spawnen findet)
docker compose build station-default 2>&1 | tail -3

# Alles starten
docker compose up -d --build 2>&1 | tail -3

log "Warte auf Services..."
sleep 5
docker compose ps 2>&1

# =============================================================================
# SSL via Certbot (optional — entkommentieren nach DNS-Propagation)
# =============================================================================
cat <<CERTBOT

┌─────────────────────────────────────────────────────────┐
│  SSL einrichten (nachdem DNS auf diese IP zeigt):       │
│                                                         │
│  apt-get install -y certbot python3-certbot-nginx       │
│  certbot --nginx -d ${DOMAIN} -d '*.${DOMAIN}'          │
│                                                         │
│  Der Wildcard-Zertifikat erfordert DNS-01 Challenge:    │
│  certbot certonly --manual --preferred-challenges dns   │
│    -d ${DOMAIN} -d '*.${DOMAIN}'                        │
│                                                         │
│  Oder via Hetzner DNS-Plugin:                           │
│  apt-get install -y certbot python3-certbot-dns-hetzner │
│  (credentials in /etc/hetzner/dns-api.ini)              │
└─────────────────────────────────────────────────────────┘
CERTBOT

# =============================================================================
# Fertig
# =============================================================================
log ""
log "================================================"
log "  RAIDO FM ist live!"
log ""
log "  Admin UI:   http://${DOMAIN}/"
log "  API:        http://${DOMAIN}/stations"
log "  Hilfe:      http://${DOMAIN}/help"
log ""
log "  Admin-Token: ${ADMIN_TOKEN}"
log "  (in .env gespeichert, chmod 600)"
log ""
log "  Logs:       docker compose -f ${APP_DIR}/docker-compose.yml logs -f"
log "  Neustart:   docker compose -f ${APP_DIR}/docker-compose.yml restart"
log "================================================"
