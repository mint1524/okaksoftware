#!/bin/sh
set -e

HTTP_TEMPLATE="/etc/nginx/templates/http.conf"
HTTPS_TEMPLATE="/etc/nginx/templates/https.conf"
TARGET="/etc/nginx/nginx.conf"

if [ -f /etc/letsencrypt/live/gpt.kcbot.ru/fullchain.pem ] \
   && [ -f /etc/letsencrypt/live/vpn.kcbot.ru/fullchain.pem ]; then
  cp "$HTTPS_TEMPLATE" "$TARGET"
  echo "[entrypoint] Loaded HTTPS configuration"
else
  cp "$HTTP_TEMPLATE" "$TARGET"
  echo "[entrypoint] Loaded HTTP-only configuration (waiting for certificates)"
fi

exec nginx -g "daemon off;"
