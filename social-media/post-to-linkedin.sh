#!/bin/bash
# Post to LinkedIn (Alvin's personal profile)
# Usage: ./post-to-linkedin.sh "Post text here"

source ~/.openclaw/secrets/linkedin-geniusmoney.env

POST_TEXT="$1"
if [ -z "$POST_TEXT" ]; then
  echo "Usage: $0 \"post text\""
  exit 1
fi

PERSON_SUB="ZtwKJ6iRot"

# Escape JSON special characters
ESCAPED=$(echo "$POST_TEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")

RESPONSE=$(curl -s -X POST "https://api.linkedin.com/v2/ugcPosts" \
  -H "Authorization: Bearer $LINKEDIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "X-Restli-Protocol-Version: 2.0.0" \
  -d "{
    \"author\": \"urn:li:person:$PERSON_SUB\",
    \"lifecycleState\": \"PUBLISHED\",
    \"specificContent\": {
      \"com.linkedin.ugc.ShareContent\": {
        \"shareCommentary\": {
          \"text\": $ESCAPED
        },
        \"shareMediaCategory\": \"ARTICLE\",
        \"media\": [{
          \"status\": \"READY\",
          \"originalUrl\": \"https://geniustax.co.uk/signup\",
          \"title\": {\"text\": \"Genius Tax — Your Tax. Sorted.\"},
          \"description\": {\"text\": \"Self-assessment from £199 upfront. MTD compliance from £299 upfront. HMRC-authorised.\"}
        }]
      }
    },
    \"visibility\": {
      \"com.linkedin.ugc.MemberNetworkVisibility\": \"PUBLIC\"
    }
  }")

POST_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','FAILED'))" 2>/dev/null)

if [ "$POST_ID" != "FAILED" ] && [ -n "$POST_ID" ]; then
  echo "SUCCESS: $POST_ID"
  # Log it
  echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"platform\":\"linkedin\",\"post_id\":\"$POST_ID\"}" >> ~/Projects/genius-tax/social-media/linkedin-post-log.json
else
  echo "FAILED: $RESPONSE"
fi
