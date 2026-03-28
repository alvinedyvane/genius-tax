#!/bin/bash
# daily-all-channels-poster.sh
# Daily cron script for Genius Tax MTD campaign.
# Called at 08:00 UK time — schedules today's posts if not already done.
#
# Cron entry:
#   0 8 * * * /Users/donnapaulsen/Projects/genius-tax/social-media/daily-all-channels-poster.sh >> /tmp/genius-tax-social.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/genius-tax-social.log"
TODAY=$(date +%Y-%m-%d)

echo ""
echo "=============================="
echo "  Genius Tax Daily Poster"
echo "  Date: $TODAY"
echo "  Time: $(date)"
echo "=============================="

cd "$SCRIPT_DIR"

# Schedule today's posts via Metricool API
# The schedule-all.py script is idempotent — safe to run multiple times
python3 "$SCRIPT_DIR/schedule-all.py" --date "$TODAY"

echo ""
echo "Daily poster complete: $(date)"
echo "=============================="
