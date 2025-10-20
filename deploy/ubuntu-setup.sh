#!/usr/bin/env bash

# Ubuntu one-command deploy for Telegram RAG bot with Traefik + Docker stack

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)

MIN_OS_SUPPORT=("22.04" "24.04")

usage() {
  echo "Usage: sudo $0 <domain> <telegram_bot_token> [letsencrypt_email] [allowed_user_ids]" >&2
  echo "Example: sudo $0 bot.example.com 123456:ABC admin@example.com" >&2
  exit 1
}

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "[ERROR] Run this script as root (sudo)." >&2
    exit 1
  fi
}

log() {
  local level="$1"; shift
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")][$level] $*"
}

check_args() {
  if [[ $# -lt 2 || $# -gt 4 ]]; then
    usage
  fi
  DOMAIN="$1"
  TELEGRAM_TOKEN="$2"
  LETSENCRYPT_EMAIL="${3:-admin@${DOMAIN}}"
  ALLOWED_USER_IDS="${4:-}"
}

check_os() {
  if [[ ! -f /etc/os-release ]]; then
    log ERROR "Cannot determine OS version (missing /etc/os-release)."
    exit 1
  fi
  . /etc/os-release
  if [[ "${ID}" != "ubuntu" ]]; then
    log ERROR "Unsupported OS: ${PRETTY_NAME}. Only Ubuntu is supported."
    exit 1
  fi
  for allowed in "${MIN_OS_SUPPORT[@]}"; do
    if [[ "${VERSION_ID}" == "${allowed}" ]]; then
      log INFO "Ubuntu ${VERSION_ID} detected."
      return
    fi
  done
  log ERROR "Unsupported Ubuntu version: ${VERSION_ID}. Supported: ${MIN_OS_SUPPORT[*]}"
  exit 1
}

ensure_dependencies() {
  log INFO "Installing base packages..."
  apt-get update
  apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release git ufw jq dnsutils rsync
}

stop_conflicting_services() {
  local services=(apache2 nginx)
  for service in "${services[@]}"; do
    if systemctl list-unit-files "${service}.service" >/dev/null 2>&1; then
      if systemctl is-active --quiet "${service}"; then
        log WARN "Stopping ${service}.service to free ports 80/443."
        systemctl stop "${service}" || log WARN "Failed to stop ${service}.service"
      fi
      if systemctl is-enabled --quiet "${service}"; then
        log INFO "Disabling ${service}.service"
        systemctl disable "${service}" >/dev/null 2>&1 || true
      fi
    fi
  done
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log INFO "Docker already installed. Skipping."
    return
  fi

  log INFO "Installing Docker CE..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg

  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" >/etc/apt/sources.list.d/docker.list

  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl enable --now docker
  log INFO "Docker installed and running."
}

check_domain_dns() {
  log INFO "Checking domain DNS resolution..."
  SERVER_IP=$(curl -4s https://ifconfig.co || curl -4s https://api.ipify.org)
  if [[ -z "${SERVER_IP}" ]]; then
    log ERROR "Failed to determine public IP."
    exit 1
  fi
  DOMAIN_IP=$(dig +short A "${DOMAIN}" @1.1.1.1 | tail -n1)
  if [[ -z "${DOMAIN_IP}" ]]; then
    log ERROR "Domain ${DOMAIN} does not have an A record."
    exit 1
  fi
  if [[ "${DOMAIN_IP}" != "${SERVER_IP}" ]]; then
    log ERROR "Domain IP (${DOMAIN_IP}) does not match server IP (${SERVER_IP}). Update DNS and retry."
    exit 1
  fi
  log INFO "Domain ${DOMAIN} resolves correctly to ${SERVER_IP}."
}

ensure_ports_free() {
  for port in 80 443; do
    if ss -tlnp | grep -q ":${port} "; then
      log ERROR "Port ${port} is occupied. Stop the conflicting service and rerun."
      exit 1
    fi
  done
  log INFO "Ports 80 and 443 are free."
}

setup_firewall() {
  if command -v ufw >/dev/null 2>&1; then
    if ufw status | grep -q "Status: active"; then
      log INFO "Configuring UFW to allow SSH, HTTP, HTTPS."
      ufw allow ssh
      ufw allow http
      ufw allow https
    else
      log INFO "UFW is inactive. Skipping firewall adjustments."
    fi
  fi
}

prepare_directories() {
  mkdir -p /opt/tgrag-bot
  mkdir -p /var/lib/tgrag-bot
  chown -R root:root /opt/tgrag-bot
}

sync_repository() {
  if [[ -d "${PROJECT_ROOT}/.git" ]]; then
    log INFO "Running inside repository clone. Syncing to /opt/tgrag-bot..."
    rsync --delete -a --exclude=.git "${PROJECT_ROOT}/" /opt/tgrag-bot/
  else
    if [[ -d /opt/tgrag-bot/.git ]]; then
      log INFO "Updating existing repository in /opt/tgrag-bot."
      git -C /opt/tgrag-bot pull --ff-only
    else
      log INFO "Cloning repository to /opt/tgrag-bot."
      git clone https://github.com/laser54/tgrag_bot.git /opt/tgrag-bot
    fi
  fi
}

write_env_file() {
  cat >/opt/tgrag-bot/.env <<EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_TOKEN}
ALLOWED_USER_IDS=${ALLOWED_USER_IDS}
WEBHOOK_DOMAIN=${DOMAIN}
WEBHOOK_URL=https://${DOMAIN}/webhook/telegram
WEBAPP_URL=https://${DOMAIN}/webapp/
PORT=8080
USE_CLOUDFLARED=false
EOF

  cat >/opt/tgrag-bot/.env.traefik <<EOF
WEBHOOK_DOMAIN=${DOMAIN}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
EOF
}

ensure_acme_store() {
  mkdir -p /opt/tgrag-bot/data/traefik
  touch /opt/tgrag-bot/data/traefik/acme.json
  chmod 600 /opt/tgrag-bot/data/traefik/acme.json
}

docker_compose_up() {
  log INFO "Starting Docker stack with Traefik..."
  pushd /opt/tgrag-bot >/dev/null
  docker compose -f docker-compose.prod.yml --env-file .env --env-file .env.traefik pull || true
  docker compose -f docker-compose.prod.yml --env-file .env --env-file .env.traefik up -d --build
  popd >/dev/null
}

wait_for_service() {
  log INFO "Waiting for bot health endpoint..."
  for attempt in {1..30}; do
    if curl -fsS "http://127.0.0.1:8080/health" >/dev/null 2>&1; then
      log INFO "Bot health endpoint is reachable."
      return
    fi
    sleep 5
  done
  log ERROR "Bot health endpoint did not become ready in time."
  exit 1
}

set_webhook() {
  log INFO "Configuring Telegram webhook..."
  payload=$(jq -n --arg url "https://${DOMAIN}/webhook/telegram" '{url: $url, drop_pending_updates: true}')
  response=$(curl -fsS -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/setWebhook" \
    -H "Content-Type: application/json" \
    -d "${payload}" || true)
  if echo "${response}" | jq -e '.ok == true' >/dev/null 2>&1; then
    log INFO "Webhook configured successfully."
  else
    log WARN "Failed to configure webhook. Response: ${response}"
  fi
}

create_systemd_unit() {
  log INFO "Creating systemd service unit..."
  cat >/etc/systemd/system/tgrag-bot.service <<'EOF'
[Unit]
Description=Telegram RAG Bot (Traefik stack)
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/opt/tgrag-bot
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml --env-file .env --env-file .env.traefik up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
Restart=always
TimeoutStartSec=0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable tgrag-bot.service
  systemctl restart tgrag-bot.service
}

print_summary() {
  cat <<EOF

----------------------------------------------------------------
Deployment complete!

- Domain: https://${DOMAIN}
- Health check (over Traefik): https://${DOMAIN}/health
- Telegram webhook URL: https://${DOMAIN}/webhook/telegram
- Compose logs: docker compose -f /opt/tgrag-bot/docker-compose.prod.yml logs -f
- Systemd logs: journalctl -u tgrag-bot -f
- Telegram webhook info: curl "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getWebhookInfo" | jq

If HTTPS failed, check Traefik logs: docker logs $(docker ps -qf "name=traefik")
----------------------------------------------------------------

EOF
}

main() {
  require_root
  check_args "$@"
  check_os
  ensure_dependencies
  stop_conflicting_services
  check_domain_dns
  ensure_ports_free
  install_docker
  setup_firewall
  prepare_directories
  sync_repository
  write_env_file
  ensure_acme_store
  docker_compose_up
  wait_for_service
  set_webhook
  create_systemd_unit
  print_summary
}

main "$@"
