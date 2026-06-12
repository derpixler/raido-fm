#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# RAIDO FM — Hetzner CX23 Setup Script
# =============================================================================
# Target:  Ubuntu 24.04 LTS, 2 vCPU, 4 GB RAM, 40 GB SSD
# DNS:     A-record raido.live → server IP, CNAME *.raido.live → raido.live
#
# Usage:   curl -fsSL https://raw.githubusercontent.com/derpixler/raido-fm/main/setup.sh | sudo bash
#          chmod +x setup.sh && sudo ./setup.sh
# =============================================================================

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[+]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[x]${NC} $*"; exit 1; }

# ── Config (override via env vars or interactive prompts) ───────────────────
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

# ── Root check ──────────────────────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] || err "Please run as root: sudo ./setup.sh"

log "RAIDO FM — Hetzner CX23 Setup"
log "================================================"
log "Domain:      ${DOMAIN}"
log "App dir:     ${APP_DIR}"
log ""

# =============================================================================
# 1. System packages
# =============================================================================
log "1/6 Installing system packages..."

apt-get update -qq
apt-get install -y -qq curl git ufw nginx 2>&1 | tail -1

if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
fi

log "System packages: OK (docker $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ','))"

# =============================================================================
# 2. Firewall
# =============================================================================
log "2/6 Configuring firewall..."

ufw --force reset >/dev/null 2>&1
ufw default deny incoming >/dev/null
ufw default allow outgoing >/dev/null
ufw allow ssh >/dev/null
ufw allow http >/dev/null
ufw allow https >/dev/null
ufw --force enable >/dev/null

log "UFW: only SSH, HTTP, HTTPS allowed"

# =============================================================================
# 3. Clone repository
# =============================================================================
log "3/6 Cloning repository..."

if [[ -d "${APP_DIR}" ]]; then
    log "Directory exists, pulling latest..."
    git -C "${APP_DIR}" pull --ff-only
else
    git clone "${GIT_REPO}" "${APP_DIR}"
fi

cd "${APP_DIR}"

# =============================================================================
# 4. Environment config
# =============================================================================
log "4/6 Configuring .env..."

if [[ ! -f .env ]]; then
    if [[ -z "${ADMIN_TOKEN}" ]]; then
        ADMIN_TOKEN=$(openssl rand -hex 32)
        log "Admin token generated: ${ADMIN_TOKEN}"
    fi

    if [[ -z "${LLM_DJ_API_KEY}" ]]; then
        warn "LLM_DJ_API_KEY is not set!"
        read -rp "DJ LLM API Key (DeepSeek/Groq): " LLM_DJ_API_KEY
    fi

    if [[ -z "${LLM_FILTER_API_KEY}" ]]; then
        warn "LLM_FILTER_API_KEY is not set! (press Enter to reuse DJ key)"
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
    log ".env created"
else
    log ".env already exists — skipping"
fi

# =============================================================================
# 5. NGINX reverse proxy
# =============================================================================
log "5/6 Configuring NGINX reverse proxy..."

cat > /etc/nginx/sites-available/raido <<NGINXEOF
# RAIDO FM — NGINX Reverse Proxy
# Hub listens internally on 127.0.0.1:${HUB_PORT}

server {
    listen 80;
    server_name ${DOMAIN} *.${DOMAIN};

    # Let's Encrypt HTTP challenge (for Certbot later)
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

        # SSE streaming support (for /s/{slug}/sse)
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

log "NGINX: listening on :80 → Hub :${HUB_PORT}"

# =============================================================================
# 6. Docker Compose build & start
# =============================================================================
log "6/6 Docker Compose: build & start..."

docker compose build station-default 2>&1 | tail -3
docker compose up -d --build 2>&1 | tail -3

log "Waiting for services..."
sleep 5
docker compose ps 2>&1

# =============================================================================
# SSL via Certbot (run manually after DNS propagation)
# =============================================================================
cat <<CERTBOT

┌─────────────────────────────────────────────────────────┐
│  Enable SSL (after DNS points to this server's IP):     │
│                                                         │
│  apt-get install -y certbot python3-certbot-nginx       │
│  certbot --nginx -d ${DOMAIN} -d '*.${DOMAIN}'          │
│                                                         │
│  Wildcard certificates require DNS-01 challenge:        │
│  certbot certonly --manual --preferred-challenges dns   │
│    -d ${DOMAIN} -d '*.${DOMAIN}'                        │
│                                                         │
│  Or via Hetzner DNS plugin:                             │
│  apt-get install -y certbot python3-certbot-dns-hetzner │
│  (store credentials in /etc/hetzner/dns-api.ini)        │
└─────────────────────────────────────────────────────────┘
CERTBOT

# =============================================================================
# Done
# =============================================================================
log ""
log "================================================"
log "  RAIDO FM is live!"
log ""
log "  Admin UI:   http://${DOMAIN}/"
log "  API:        http://${DOMAIN}/stations"
log "  Help:       http://${DOMAIN}/help"
log ""
log "  Admin token: ${ADMIN_TOKEN}"
log "  (stored in .env, chmod 600)"
log ""
log "  Logs:       docker compose -f ${APP_DIR}/docker-compose.yml logs -f"
log "  Restart:    docker compose -f ${APP_DIR}/docker-compose.yml restart"
log "================================================"
