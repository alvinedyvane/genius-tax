#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
# ============================================================
# GeniusTax — Local Ads Status Reminder
# ============================================================
# This is a LOCAL companion script to the Google Ads Script.
# The real monitoring (with direct account access) lives in:
#   ~/Projects/genius-tax/google-ads-monitor.js
#   → paste that into Google Ads → Tools → Scripts → Schedule Daily
#
# This script:
#   1. Sends a Telegram reminder to the main session so the
#      daily email from Google Ads Scripts isn't missed
#   2. Can be expanded to call the Google Ads API directly
#      (requires OAuth setup — not needed while the JS script is active)
#
# CRON SETUP (runs daily at 8am AST = 12:00 UTC):
#   crontab -e
#   Add this line:
#   0 12 * * * /Users/donnapaulsen/Projects/genius-tax/check-ads-status.sh >> /tmp/genius-tax-ads-cron.log 2>&1
#
# ============================================================

set -euo pipefail

LOG_PREFIX="[GeniusTax Ads Check] $(date '+%Y-%m-%d %H:%M:%S AST')"
OPENCLAW_BIN="/opt/homebrew/bin/openclaw"
TELEGRAM_TARGET="1095557418"   # Alvin's Telegram ID

# ── Log to stdout (captured by cron) ──────────────────────
echo "$LOG_PREFIX — Running daily ads reminder"

# ── Build reminder message ─────────────────────────────────
MESSAGE="📊 *GeniusTax Daily Ads Check*

This is your 8am reminder that the Google Ads monitor script runs daily.

✅ Check your inbox (alvin@geniusmoney.co.uk) for the GeniusTax Ads daily email.

If the subject says ⚠️ *ACTION NEEDED* — log in to Google Ads now:
🔗 https://ads.google.com

Campaigns monitored:
• \[GeniusTax\] MTD High-Intent Search
• \[GeniusTax\] MTD Awareness Search
• \[GeniusTax\] Audience-Specific Search
• \[GeniusTax\] Competitor Conquest

Account: 513-572-0126"

# ── Send via openclaw ──────────────────────────────────────
if [ -x "$OPENCLAW_BIN" ]; then
  echo "$LOG_PREFIX — Sending Telegram reminder to $TELEGRAM_TARGET"
  "$OPENCLAW_BIN" message send \
    --channel telegram \
    --target "$TELEGRAM_TARGET" \
    --message "$MESSAGE" \
    && echo "$LOG_PREFIX — Telegram message sent OK" \
    || echo "$LOG_PREFIX — WARNING: Telegram send failed (check openclaw gateway)"
else
  echo "$LOG_PREFIX — WARNING: openclaw not found at $OPENCLAW_BIN"
  echo "$LOG_PREFIX — Skipping Telegram notification"
fi

echo "$LOG_PREFIX — Done"
