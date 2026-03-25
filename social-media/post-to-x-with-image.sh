#!/usr/bin/env bash
# post-to-x-with-image.sh — Post a tweet with an image via X API v2
# Usage: ./post-to-x-with-image.sh "Your tweet text" /path/to/image.png
# If no image path given, posts text only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/x-post-log.json"
ENV_FILE="$HOME/.openclaw/secrets/x-geniustax.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: Env file not found: $ENV_FILE" >&2
  exit 1
fi
source "$ENV_FILE"

if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "Usage: $0 \"tweet text\" [/path/to/image.png]" >&2
  exit 1
fi

TWEET_TEXT="$1"
IMAGE_PATH="${2:-}"

RESPONSE=$(python3 - <<PYEOF
import sys, json, os
from requests_oauthlib import OAuth1Session

consumer_key        = "$X_CONSUMER_KEY"
consumer_secret     = "$X_SECRET_KEY"
access_token        = "$X_ACCESS_TOKEN"
access_token_secret = "$X_ACCESS_TOKEN_SECRET"

tweet_text = """${TWEET_TEXT}"""
image_path = """${IMAGE_PATH}"""

oauth = OAuth1Session(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=access_token,
    resource_owner_secret=access_token_secret,
)

media_id = None

# Upload image if provided (simple upload for images under 5MB)
if image_path and os.path.isfile(image_path):
    with open(image_path, "rb") as f:
        upload_resp = oauth.post(
            "https://upload.twitter.com/1.1/media/upload.json",
            files={"media": f}
        )
    if upload_resp.status_code not in (200, 201, 202):
        print(json.dumps({"status_code": upload_resp.status_code, "body": {"error": f"Upload failed: {upload_resp.text}"}}))
        sys.exit(0)
    media_id = upload_resp.json()["media_id_string"]

# Post tweet
payload = {"text": tweet_text}
if media_id:
    payload["media"] = {"media_ids": [media_id]}

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

python3 - <<PYEOF
import json
log_file = "$LOG_FILE"
try:
    with open(log_file, "r") as f:
        log = json.load(f)
    if not isinstance(log, list): log = []
except: log = []

entry = {
    "timestamp": "$TIMESTAMP",
    "tweet_text": """${TWEET_TEXT}""",
    "image": """${IMAGE_PATH}""",
    "status_code": $STATUS_CODE,
    "response": $(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['body']))")
}
log.append(entry)
with open(log_file, "w") as f:
    json.dump(log, f, indent=2)
PYEOF

if [[ "$STATUS_CODE" == "201" ]]; then
  echo "✅ Tweet posted! ID: $TWEET_ID"
  exit 0
else
  echo "❌ Failed (HTTP $STATUS_CODE)" >&2
  echo "   $RESPONSE" >&2
  exit 1
fi
