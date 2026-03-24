#!/usr/bin/env bash
# daily-x-poster.sh — Find today's X/Twitter content and post it
# Usage: ./daily-x-poster.sh
# Designed to be run via cron, e.g.:
#   0 9 * * * /path/to/daily-x-poster.sh >> /path/to/daily-x-poster.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CALENDAR_FILE="$SCRIPT_DIR/content-calendar.md"
POST_SCRIPT="$SCRIPT_DIR/post-to-x.sh"

# ── Validate dependencies ──────────────────────────────────────────────────────
if [[ ! -f "$CALENDAR_FILE" ]]; then
  echo "ERROR: Content calendar not found: $CALENDAR_FILE" >&2
  exit 1
fi

if [[ ! -x "$POST_SCRIPT" ]]; then
  echo "ERROR: post-to-x.sh not found or not executable: $POST_SCRIPT" >&2
  exit 1
fi

# ── Get today's date in calendar format (e.g. "March 24, 2026") ───────────────
TODAY_DATE=$(date "+%B %-d, %Y")
TODAY_ISO=$(date "+%Y-%m-%d")

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] daily-x-poster: Checking for $TODAY_DATE content..."

# ── Extract today's X/Twitter entry from the calendar ─────────────────────────
TWEET_TEXT=$(python3 - <<PYEOF
import re, sys

calendar_file = "$CALENDAR_FILE"
today = "$TODAY_DATE"

with open(calendar_file, "r") as f:
    content = f.read()

# Split into date sections
sections = re.split(r'^##\s+', content, flags=re.MULTILINE)

tweet = None
for section in sections:
    lines = section.strip().splitlines()
    if not lines:
        continue
    # First line of each section is the date header
    section_date = lines[0].strip()
    if section_date == today:
        # Find the X/Twitter line
        for line in lines[1:]:
            if line.startswith("**X/Twitter:**"):
                tweet = line.replace("**X/Twitter:**", "").strip()
                break
        break

if tweet:
    print(tweet)
else:
    print("")
PYEOF
)

# ── Fallback: generate a generic countdown tweet ───────────────────────────────
if [[ -z "$TWEET_TEXT" ]]; then
  echo "No content found for $TODAY_DATE — generating countdown tweet..."

  DAYS_LEFT=$(python3 - <<PYEOF
from datetime import date
target = date(2026, 4, 5)
today = date.today()
delta = (target - today).days
print(max(delta, 0))
PYEOF
)

  if [[ "$DAYS_LEFT" -gt 0 ]]; then
    TWEET_TEXT="⏰ Just $DAYS_LEFT days until MTD goes live on April 5, 2026! Is your business ready? Genius Tax makes compliance simple. Sign up today. #GeniusTax #MTD #MakingTaxDigital"
  else
    TWEET_TEXT="MTD is live! Is your business compliant? Genius Tax is here to help you navigate Making Tax Digital with ease. #GeniusTax #MTD #MakingTaxDigital"
  fi
fi

echo "Posting: $TWEET_TEXT"
"$POST_SCRIPT" "$TWEET_TEXT"
