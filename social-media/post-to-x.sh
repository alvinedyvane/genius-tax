#!/usr/bin/env bash
# post-to-x.sh — Post a tweet via X API v2 with OAuth 1.0a
# Usage: ./post-to-x.sh "Your tweet text here"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/x-post-log.json"
ENV_FILE="$HOME/.openclaw/secrets/x-geniustax.env"

# ── Load API keys ──────────────────────────────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: Env file not found: $ENV_FILE" >&2
  exit 1
fi
# shellcheck source=/dev/null
source "$ENV_FILE"

# ── Validate args ──────────────────────────────────────────────────────────────
if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "Usage: $0 \"tweet text here\"" >&2
  exit 1
fi

TWEET_TEXT="$1"

# ── Post via Python OAuth 1.0a ─────────────────────────────────────────────────
RESPONSE=$(python3 - <<PYEOF
import sys, json
from requests_oauthlib import OAuth1Session

consumer_key        = "$X_CONSUMER_KEY"
consumer_secret     = "$X_SECRET_KEY"
access_token        = "$X_ACCESS_TOKEN"
access_token_secret = "$X_ACCESS_TOKEN_SECRET"

tweet_text = """${TWEET_TEXT}"""

oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

payload = {"text": tweet_text}

resp = oauth.post("https://api.twitter.com/2/tweets", json=payload)
print(json.dumps({
    "status_code": resp.status_code,
    "body": resp.json()
}))
PYEOF
)

STATUS_CODE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status_code'])")
TWEET_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['body'].get('data',{}).get('id',''))" 2>/dev/null || echo "")

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Append to log ──────────────────────────────────────────────────────────────
LOG_ENTRY=$(python3 - <<PYEOF
import json, sys

log_file = "$LOG_FILE"
try:
    with open(log_file, "r") as f:
        log = json.load(f)
    if not isinstance(log, list):
        log = []
except (FileNotFoundError, json.JSONDecodeError):
    log = []

entry = {
    "timestamp": "$TIMESTAMP",
    "tweet_text": """${TWEET_TEXT}""",
    "status_code": $STATUS_CODE,
    "response": $(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['body']))")
}
log.append(entry)

with open(log_file, "w") as f:
    json.dump(log, f, indent=2)

print("logged")
PYEOF
)

# ── Result ─────────────────────────────────────────────────────────────────────
if [[ "$STATUS_CODE" == "201" ]]; then
  echo "✅ Tweet posted! ID: $TWEET_ID"
  echo "   Text: $TWEET_TEXT"
  exit 0
else
  echo "❌ Failed to post tweet (HTTP $STATUS_CODE)" >&2
  echo "   Response: $RESPONSE" >&2
  exit 1
fi
