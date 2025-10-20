#!/usr/bin/env bash
# Download and run ubuntu-setup.sh from GitHub. Supports local checkout fallback.

set -euo pipefail

RAW_URL=${RAW_URL:-https://raw.githubusercontent.com/laser54/tgrag_bot/main/deploy/ubuntu-setup.sh}

if [[ $# -lt 2 ]]; then
  echo "Usage: curl -fsSL ${RAW_URL%/ubuntu-setup.sh}/bootstrap.sh | sudo bash -s -- <domain> <telegram_token> [letsencrypt_email] [allowed_user_ids]" >&2
  exit 1
fi

TMP_SCRIPT=$(mktemp)
trap 'rm -f "$TMP_SCRIPT"' EXIT

if command -v curl >/dev/null 2>&1; then
  curl -fsSL "${RAW_URL}" -o "$TMP_SCRIPT"
else
  echo "curl is required" >&2
  exit 1
fi

chmod +x "$TMP_SCRIPT"
"$TMP_SCRIPT" "$@"
