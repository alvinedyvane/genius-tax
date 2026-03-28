#!/usr/bin/env bash
# daily-meta-poster.sh — Post today's Instagram content to Facebook + Instagram via Metricool API
#
# Usage: ./daily-meta-poster.sh [--dry-run]
#
# Reads today's Instagram Post 1 from content-calendar.md, picks a branded image,
# and schedules it 1 minute from now via metricool-api-poster.py.
#
# Designed to be run via cron:
#   0 9 * * * /path/to/daily-meta-poster.sh >> /tmp/daily-meta-poster.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CALENDAR_FILE="$SCRIPT_DIR/content-calendar.md"
POSTER_SCRIPT="$SCRIPT_DIR/metricool-api-poster.py"
IMAGES_DIR="$SCRIPT_DIR/images/branded"
ROTATION_STATE="$SCRIPT_DIR/image-rotation-state.json"

DRY_RUN=""
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN="--dry-run"
fi

# ── Validate ───────────────────────────────────────────────────────────────────
if [[ ! -f "$CALENDAR_FILE" ]]; then
  echo "ERROR: Content calendar not found: $CALENDAR_FILE" >&2
  exit 1
fi

if [[ ! -f "$POSTER_SCRIPT" ]]; then
  echo "ERROR: Poster script not found: $POSTER_SCRIPT" >&2
  exit 1
fi

# ── Get today's date ───────────────────────────────────────────────────────────
TODAY_DATE=$(date "+%B %-d, %Y" | sed 's/^//' )  # e.g. "March 26, 2026"
TODAY_UPPER=$(echo "$TODAY_DATE" | tr '[:lower:]' '[:upper:]')   # e.g. "MARCH 26, 2026"
NOW_PLUS_2=$(date -v+2M "+%Y-%m-%d %H:%M" 2>/dev/null || date -d "+2 minutes" "+%Y-%m-%d %H:%M")

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] daily-meta-poster: Checking for $TODAY_DATE content..."

# ── Extract today's first Instagram post from calendar ─────────────────────────
POST_TEXT=$(python3 - <<PYEOF
import re, sys

calendar_file = "$CALENDAR_FILE"
today_upper = "$TODAY_UPPER"

with open(calendar_file, "r") as f:
    content = f.read()

# Find today's section header (format: ## MARCH 26, 2026 — ...)
# Try matching the date with flexible spacing
lines = content.splitlines()
section_start = None
section_end = None

for i, line in enumerate(lines):
    if line.startswith("## "):
        # Strip leading ## and check if it contains today's date
        header = line[3:].strip()
        # Check if line contains today's date (may have trailing — notes)
        if today_upper in header.upper():
            section_start = i
        elif section_start is not None:
            section_end = i
            break

if section_start is None:
    sys.exit(0)  # No content for today

if section_end is None:
    section_end = len(lines)

section = "\n".join(lines[section_start:section_end])

# Find ### Instagram subsection
ig_match = re.search(r'### Instagram\n(.*?)(?=###|\Z)', section, re.DOTALL)
if not ig_match:
    sys.exit(0)

ig_text = ig_match.group(1)

# Extract first post block: **Post 1:** ... until **Post 2:** or end
post_match = re.search(r'\*\*Post 1:\*\*\s*\n(.*?)(?=\*\*Post \d+:\*\*|---|\Z)', ig_text, re.DOTALL)
if not post_match:
    sys.exit(0)

text = post_match.group(1).strip()
# Remove trailing --- separator
text = re.sub(r'\n---\s*$', '', text).strip()
print(text)
PYEOF
)

if [[ -z "$POST_TEXT" ]]; then
  echo "No Instagram content found for $TODAY_DATE — skipping"
  exit 0
fi

# ── Pick branded image (rotate through images) ────────────────────────────────
IMAGES=(
  "01-your-tax-sorted.png"
  "02-built-for-people.png"
  "03-three-steps.png"
  "04-simple-pricing.png"
  "06-pick-your-plan.png"
  "07-ready-sorted.png"
)

# Use day-of-year for rotation
DOY=$(date "+%j" | sed 's/^0*//')
IMG_IDX=$(( DOY % ${#IMAGES[@]} ))
IMAGE_FILE="$IMAGES_DIR/${IMAGES[$IMG_IDX]}"

if [[ ! -f "$IMAGE_FILE" ]]; then
  echo "WARNING: Image not found: $IMAGE_FILE — posting without image"
  IMAGE_ARG=""
else
  IMAGE_ARG="--image $IMAGE_FILE"
fi

# ── Post it ────────────────────────────────────────────────────────────────────
echo "Posting to Facebook + Instagram for $TODAY_DATE"
echo "Image: ${IMAGE_FILE:-none}"
echo "Schedule: $NOW_PLUS_2 UK"
echo "Text preview: ${POST_TEXT:0:80}..."

python3 "$POSTER_SCRIPT" \
  --text "$POST_TEXT" \
  ${IMAGE_ARG:-} \
  --schedule "$NOW_PLUS_2" \
  --channels "facebook,instagram" \
  ${DRY_RUN}

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] daily-meta-poster: Done"
