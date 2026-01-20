#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
EMAIL="${EMAIL:-teacher@endowal.app}"
PASSWORD="${PASSWORD:-Teacher123!}"

echo "Using BASE_URL=$BASE_URL"
echo "Logging in as $EMAIL"

TOKEN=$(
  curl -s "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
    | python - <<'PY'
import json, sys
data = json.load(sys.stdin)
print(data.get("access_token", ""))
PY
)

if [[ -z "$TOKEN" ]]; then
  echo "Login failed. Check credentials or seed data."
  exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"

echo "GET /auth/me"
curl -s "$BASE_URL/auth/me" -H "$AUTH_HEADER" | python -m json.tool

echo "GET /classrooms"
CLASSROOM_ID=$(
  curl -s "$BASE_URL/classrooms" -H "$AUTH_HEADER" \
    | python - <<'PY'
import json, sys
items = json.load(sys.stdin)
print(items[0]["id"] if items else "")
PY
)
echo "Classroom ID: $CLASSROOM_ID"

echo "GET /assignments"
curl -s "$BASE_URL/assignments" -H "$AUTH_HEADER" | python -m json.tool

echo "GET /wallets"
WALLET_ID=$(
  curl -s "$BASE_URL/wallets" -H "$AUTH_HEADER" \
    | python - <<'PY'
import json, sys
items = json.load(sys.stdin)
print(items[0]["id"] if items else "")
PY
)
echo "Wallet ID: $WALLET_ID"

if [[ -n "$WALLET_ID" ]]; then
  echo "GET /buckets?wallet_id=$WALLET_ID"
  curl -s "$BASE_URL/buckets?wallet_id=$WALLET_ID" -H "$AUTH_HEADER" | python -m json.tool

  echo "GET /ledger-entries?wallet_id=$WALLET_ID"
  curl -s "$BASE_URL/ledger-entries?wallet_id=$WALLET_ID" -H "$AUTH_HEADER" | python -m json.tool
fi
