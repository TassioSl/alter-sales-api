#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://alter-sales-api-1.onrender.com}"
API_USERNAME="biomundo_api"
API_PASSWORD="B!oMundo_2026_R3nder_A7kP9xLm"

echo "GET ${BASE_URL}/"
curl -sS "${BASE_URL}/"
printf '\n\n'

echo "GET ${BASE_URL}/api/health"
curl -sS -u "${API_USERNAME}:${API_PASSWORD}" "${BASE_URL}/api/health"
printf '\n\n'

echo "GET ${BASE_URL}/api/sales/latest"
curl -sS -u "${API_USERNAME}:${API_PASSWORD}" "${BASE_URL}/api/sales/latest"
printf '\n\n'

echo "GET ${BASE_URL}/api/alter/feed/per-hour"
curl -sS -u "${API_USERNAME}:${API_PASSWORD}" "${BASE_URL}/api/alter/feed/per-hour"
printf '\n\n'

echo "GET ${BASE_URL}/api/alter/feed/per-store"
curl -sS -u "${API_USERNAME}:${API_PASSWORD}" "${BASE_URL}/api/alter/feed/per-store"
printf '\n'
