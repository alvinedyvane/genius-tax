#!/usr/bin/env python3
"""
schedule-all.py
Schedules ALL Genius Tax MTD campaign posts for Mar 26 – Apr 4, 2026
via Metricool API — Twitter, Instagram, LinkedIn, TikTok simultaneously.

Posts 3 per day at UK times: 07:45 / 11:30 / 16:00
Idempotent: skips any date/time already in the log.

Usage:
  python3 schedule-all.py           # schedule everything
  python3 schedule-all.py --dry-run # preview without posting
  python3 schedule-all.py --date 2026-03-27  # schedule only one day
"""

import argparse
import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─── Config ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DATA_DIR    = BASE_DIR / "data"
LOG_FILE    = DATA_DIR / "metricool-api-log.json"
SECRETS_FILE = Path.home() / ".openclaw" / "secrets" / "metricool.env"
IMAGE_DIR   = BASE_DIR / "images" / "branded"
IMAGE_CACHE = DATA_DIR / "image-url-cache.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://app.metricool.com/api"
IMGUR_CLIENT_ID = "546c25a59c58ad7"
TIMEZONE = "Europe/London"

# Channels — Twitter, Instagram, LinkedIn, TikTok (no Facebook)
ALL_CHANNELS = [
    {"network": "twitter",   "id": "geniusmoneyltd"},
    {"network": "instagram", "id": "17841403854498977"},
    {"network": "linkedin",  "id": "urn:li:organization:2629878"},
    {"network": "tiktok",    "id": "genius.money10"},
]

# Approved images — rotated so no image repeats within 3 days
IMAGES = [
    "branded-hero-square.png",
    "01-your-tax-sorted.png",
    "02-built-for-people.png",
    "03-three-steps.png",
    "04-simple-pricing.png",
    "06-pick-your-plan.png",
    "07-ready-sorted.png",
    "08-linkedin-hero.png",
    "09-pricing-detailed.png",
    "10-pricing-5pw-landscape.png",
    "10-pricing-5pw-square.png",
    "branded-pricing-square.png",
    "branded-steps-square.png",
]

# ─── Content Schedule ──────────────────────────────────────────────────────────
# 3 posts per day at 07:45 / 11:30 / 16:00 UK time
# Images rotate in groups of 3, no image repeats within 3 days
# Copy is human-sounding, British tone, no emojis, no bullet points
# Correct pricing: from £20/month | Essential £199/year | Growth Yr1 £299/year | Growth Yr2 £500/year
# MTD mandatory April 2026 for £50k+ income, April 2027 for £30k+

SCHEDULE = [
    # ── Mar 26 — Introducing Making Tax Digital ────────────────────────────────
    {
        "date": "2026-03-26",
        "time": "07:45",
        "image": "branded-hero-square.png",
        "text": (
            "Making Tax Digital for Income Tax is live from April 2026. "
            "If your income from self-employment or property is over fifty thousand pounds a year, "
            "quarterly digital filings with HMRC are now a legal requirement. "
            "Genius Tax handles all of it, registration, software, every submission, "
            "for a flat annual fee starting from one hundred and ninety-nine pounds. "
            "Have a look at geniustax.co.uk and see which plan suits you."
        ),
    },
    {
        "date": "2026-03-26",
        "time": "11:30",
        "image": "01-your-tax-sorted.png",
        "text": (
            "Self-assessment as most people know it is changing. "
            "From April 2026, anyone earning over fifty thousand pounds from self-employment or property "
            "needs to file quarterly updates with HMRC rather than a single annual return. "
            "You also need HMRC-approved software to do it. "
            "Genius Tax takes care of all of this, including Sage, so you do not have to think about it. "
            "Plans from £20 a month at geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-26",
        "time": "16:00",
        "image": "02-built-for-people.png",
        "text": (
            "Genius Tax was built for people who want their tax compliance sorted "
            "without having to become experts in it themselves. "
            "Making Tax Digital means four quarterly submissions to HMRC each year, "
            "plus a final year-end declaration, all using approved software. "
            "We handle every bit of that on your behalf. "
            "Essential is one hundred and ninety-nine pounds a year, "
            "Growth is two hundred and ninety-nine in year one. "
            "geniustax.co.uk"
        ),
    },

    # ── Mar 27 — Self-employed and freelancers ─────────────────────────────────
    {
        "date": "2026-03-27",
        "time": "07:45",
        "image": "03-three-steps.png",
        "text": (
            "If you are self-employed and your annual income is over fifty thousand pounds, "
            "Making Tax Digital applies to you from April 2026. "
            "The process involves quarterly updates to HMRC, a final declaration at year end, "
            "and HMRC-approved software to manage it all. "
            "Genius Tax does the registration, the Sage setup, and every filing throughout the year. "
            "From £20 a month at geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-27",
        "time": "11:30",
        "image": "04-simple-pricing.png",
        "text": (
            "Getting set up with Genius Tax is straightforward. "
            "We register as your HMRC Authorised Agent, get you onto Sage accounting software, "
            "and from there we manage your quarterly submissions and year-end declaration. "
            "You share your income and expense records with us each quarter, we do everything else. "
            "Essential plan is one hundred and ninety-nine pounds a year, "
            "Growth year one is two hundred and ninety-nine. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-27",
        "time": "16:00",
        "image": "06-pick-your-plan.png",
        "text": (
            "Freelancers, consultants, sole traders. "
            "If your income is over fifty thousand pounds, Making Tax Digital is not optional from April 2026. "
            "That means quarterly digital filings, HMRC-approved software, and proper registration. "
            "Genius Tax is an HMRC Authorised Agent, Sage software is included on all plans, "
            "and we manage everything for you. "
            "Pick the plan that fits at geniustax.co.uk, from £20 a month."
        ),
    },

    # ── Mar 28 — How MTD works and what penalties look like ───────────────────
    {
        "date": "2026-03-28",
        "time": "07:45",
        "image": "07-ready-sorted.png",
        "text": (
            "Making Tax Digital replaces the annual self-assessment return with quarterly updates. "
            "Instead of one big filing in January, you submit a summary of income and expenses "
            "four times a year and a final declaration at year end. "
            "The software needs to be HMRC-approved, which is where most people trip up. "
            "Genius Tax handles the whole thing, Sage included, for a flat annual fee. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-28",
        "time": "11:30",
        "image": "08-linkedin-hero.png",
        "text": (
            "HMRC's penalty system for MTD non-compliance is points-based, "
            "which means it compounds over time. "
            "Late or missed quarterly submissions add up, and the fines escalate with each one. "
            "Getting registered and compliant before April 2026 removes that risk entirely. "
            "Genius Tax handles the whole compliance process for a flat fee, "
            "from £20 a month or one hundred and ninety-nine pounds a year on the Essential plan. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-28",
        "time": "16:00",
        "image": "09-pricing-detailed.png",
        "text": (
            "Genius Tax offers three straightforward options. "
            "You can pay monthly from £20 a month, "
            "or annually on the Essential plan at one hundred and ninety-nine pounds, "
            "or the Growth plan at two hundred and ninety-nine in year one "
            "and five hundred from year two. "
            "All plans include HMRC registration, Sage accounting software, "
            "quarterly filing management, and your year-end declaration. "
            "No hidden extras at all. "
            "geniustax.co.uk"
        ),
    },

    # ── Mar 29 — Landlords and property income ─────────────────────────────────
    {
        "date": "2026-03-29",
        "time": "07:45",
        "image": "10-pricing-5pw-landscape.png",
        "text": (
            "Landlords with rental income over fifty thousand pounds are within scope "
            "for Making Tax Digital from April 2026. "
            "This includes income from residential and commercial property. "
            "Quarterly digital submissions to HMRC are required, using approved software "
            "and ideally with an authorised agent managing it on your behalf. "
            "That is exactly what Genius Tax provides. "
            "From £20 a month at geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-29",
        "time": "11:30",
        "image": "10-pricing-5pw-square.png",
        "text": (
            "The most common question from landlords: does Making Tax Digital apply to me? "
            "If your total qualifying income, which includes rental income and any self-employment income, "
            "is over fifty thousand pounds, yes, from April 2026. "
            "If it is over thirty thousand, the same applies from April 2027. "
            "Genius Tax makes the compliance side completely straightforward. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-29",
        "time": "16:00",
        "image": "branded-pricing-square.png",
        "text": (
            "Some landlords run property alongside a limited company or other business interests "
            "and assume their accountant has it all covered. Worth checking. "
            "Making Tax Digital for personal income, including rental income, "
            "is a separate obligation that requires specific registration, "
            "approved software and quarterly filings. "
            "Genius Tax specialises in exactly this. "
            "Essential one hundred and ninety-nine a year, Growth from two hundred and ninety-nine. "
            "geniustax.co.uk"
        ),
    },

    # ── Mar 30 — The process and value of getting it sorted ───────────────────
    {
        "date": "2026-03-30",
        "time": "07:45",
        "image": "branded-steps-square.png",
        "text": (
            "Making Tax Digital compliance comes down to three things. "
            "Being registered with HMRC, having approved software in place, "
            "and submitting four quarterly updates plus a year-end declaration. "
            "Genius Tax handles all three as your HMRC Authorised Agent. "
            "The whole thing costs less than most people spend on a takeaway each week, "
            "from five pounds on the monthly plan. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-30",
        "time": "11:30",
        "image": "branded-hero-square.png",
        "text": (
            "A lot of people assume their existing accountant is handling MTD automatically. "
            "That may not be the case. "
            "Making Tax Digital requires active registration with HMRC, approved software, "
            "and quarterly filings, and not all accountants have set this up for clients yet. "
            "If you are not sure where you stand, Genius Tax can step in "
            "and take over the whole thing for a flat fee from £20 a month. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-30",
        "time": "16:00",
        "image": "01-your-tax-sorted.png",
        "text": (
            "The way Genius Tax works in practice is simple. "
            "At the end of each quarter you share your income and expense records with us, "
            "we enter them into Sage and file the quarterly update with HMRC, "
            "and you receive confirmation that it is done. "
            "Year end follows the same pattern. "
            "No chasing, no last-minute stress, no surprises. "
            "Plans from £20 a month. "
            "geniustax.co.uk"
        ),
    },

    # ── Mar 31 — Six days to go ────────────────────────────────────────────────
    {
        "date": "2026-03-31",
        "time": "07:45",
        "image": "02-built-for-people.png",
        "text": (
            "Six days until Making Tax Digital is live for incomes over fifty thousand pounds. "
            "If you earn over that threshold from self-employment or property "
            "and have not sorted your compliance yet, this week is the week to do it. "
            "Genius Tax can still get you registered with HMRC and set up on Sage "
            "before April sixth. "
            "Plans from £20 a month at geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-31",
        "time": "11:30",
        "image": "03-three-steps.png",
        "text": (
            "Last day of March and six days until the MTD deadline. "
            "Essential plan is one hundred and ninety-nine pounds a year, "
            "Growth is two hundred and ninety-nine in year one "
            "or five hundred from year two, "
            "and monthly plans start from £20 a month. "
            "If you have been meaning to get this sorted before April, "
            "today is a sensible day to do it. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-03-31",
        "time": "16:00",
        "image": "04-simple-pricing.png",
        "text": (
            "End of March. Six days until Making Tax Digital goes live "
            "for anyone earning over fifty thousand from self-employment or property. "
            "Genius Tax keeps the process simple: you join, we handle HMRC registration, "
            "Sage setup, and every filing throughout the year. "
            "You just need to share your records with us each quarter and we do the rest. "
            "From one hundred and ninety-nine a year. "
            "geniustax.co.uk"
        ),
    },

    # ── Apr 1 — Five days, contractors in focus ────────────────────────────────
    {
        "date": "2026-04-01",
        "time": "07:45",
        "image": "06-pick-your-plan.png",
        "text": (
            "Five days until Making Tax Digital is live. "
            "If your income from self-employment or property is over fifty thousand pounds "
            "and you are not yet registered with an HMRC Authorised Agent and on approved software, "
            "this is the week to sort it. "
            "Genius Tax can still get everything in place before the deadline. "
            "From £20 a month at geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-01",
        "time": "11:30",
        "image": "07-ready-sorted.png",
        "text": (
            "Contractors and tradespeople earning over fifty thousand pounds, "
            "Making Tax Digital applies to you too. "
            "Self-employed income through any route, "
            "whether sole trader, CIS work or otherwise, counts toward the threshold. "
            "Genius Tax handles the MTD obligations for contractors properly, "
            "including registration, Sage setup and quarterly filings. "
            "Five days left. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-01",
        "time": "16:00",
        "image": "08-linkedin-hero.png",
        "text": (
            "The cost of getting MTD compliance sorted with Genius Tax "
            "is one hundred and ninety-nine pounds a year on the Essential plan. "
            "The cost of not getting it sorted starts with an HMRC penalty "
            "and escalates with every missed quarterly submission under the points-based system. "
            "The maths are not complicated. "
            "Five days left. "
            "geniustax.co.uk"
        ),
    },

    # ── Apr 2 — Three days, urgency rising ────────────────────────────────────
    {
        "date": "2026-04-02",
        "time": "07:45",
        "image": "09-pricing-detailed.png",
        "text": (
            "Three days until Making Tax Digital is live for incomes over fifty thousand pounds. "
            "If you have been putting this off, today is realistically the last sensible day "
            "to get the process started. "
            "Genius Tax can still onboard you and get your HMRC registration in place "
            "before April sixth, but capacity is limited this week. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-02",
        "time": "11:30",
        "image": "10-pricing-5pw-landscape.png",
        "text": (
            "Three days to go before MTD is live. "
            "Quarterly digital filing is a legal requirement for anyone "
            "with self-employment or property income over fifty thousand pounds from April 2026. "
            "Genius Tax is an HMRC Authorised Agent, Sage is included on all plans, "
            "and the quarterly filings are fully managed on your behalf. "
            "Essential at one hundred and ninety-nine a year, "
            "Growth at two hundred and ninety-nine. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-02",
        "time": "16:00",
        "image": "10-pricing-5pw-square.png",
        "text": (
            "If you know someone who is self-employed or earns rental income over fifty thousand pounds, "
            "please share this with them. "
            "Making Tax Digital is live in three days "
            "and a lot of people in scope have still not taken action. "
            "Genius Tax from £20 a month, full MTD compliance handled for you. "
            "geniustax.co.uk"
        ),
    },

    # ── Apr 3 — Two days, final warning ───────────────────────────────────────
    {
        "date": "2026-04-03",
        "time": "07:45",
        "image": "branded-pricing-square.png",
        "text": (
            "Two days. Making Tax Digital is live on April sixth "
            "for anyone earning over fifty thousand pounds from self-employment or property. "
            "If you are not yet registered with an HMRC Authorised Agent and on approved software, "
            "you need to act today. "
            "We are still accepting new clients but that will not remain the case much longer. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-03",
        "time": "11:30",
        "image": "branded-steps-square.png",
        "text": (
            "Tomorrow is the last full day before the MTD deadline. "
            "If you sign up with Genius Tax today "
            "we can still complete your HMRC registration and Sage setup before April sixth. "
            "After that, the opportunity to get compliant without penalty shrinks significantly. "
            "Monthly plans from £20 a month, annual from one hundred and ninety-nine. "
            "geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-03",
        "time": "16:00",
        "image": "branded-hero-square.png",
        "text": (
            "Two days until Making Tax Digital is live "
            "and HMRC's penalty framework is unambiguous. "
            "Miss your registration and quarterly obligations "
            "and the fines accumulate under the points system with every missed submission. "
            "Getting compliant now is cheaper, simpler, and a lot less stressful. "
            "Genius Tax, HMRC Authorised, Sage included, full service from £20 a month. "
            "geniustax.co.uk"
        ),
    },

    # ── Apr 4 — Final day ──────────────────────────────────────────────────────
    {
        "date": "2026-04-04",
        "time": "07:45",
        "image": "01-your-tax-sorted.png",
        "text": (
            "Today is April fourth. "
            "Making Tax Digital goes live tomorrow for anyone earning over fifty thousand pounds "
            "from self-employment or property. "
            "If you are not yet compliant, today is your last realistic chance to sort it. "
            "Genius Tax is still taking sign-ups. "
            "Get registered and sorted at geniustax.co.uk before the deadline."
        ),
    },
    {
        "date": "2026-04-04",
        "time": "11:30",
        "image": "02-built-for-people.png",
        "text": (
            "Last chance to get your MTD compliance in place before tomorrow's deadline. "
            "Genius Tax Essential is one hundred and ninety-nine pounds a year, "
            "Growth is two hundred and ninety-nine in year one and five hundred from year two, "
            "or you can pay monthly from £20 a month. "
            "HMRC registration, Sage software and all quarterly filings included. "
            "Sign up today at geniustax.co.uk"
        ),
    },
    {
        "date": "2026-04-04",
        "time": "16:00",
        "image": "03-three-steps.png",
        "text": (
            "The MTD deadline is tomorrow. "
            "For anyone earning over fifty thousand pounds from self-employment or property, "
            "quarterly digital filing is a legal requirement from April sixth. "
            "It is not too late, but you need to act in the next few hours. "
            "Genius Tax at geniustax.co.uk, from £20 a month, properly sorted."
        ),
    },
]


# ─── Credentials ───────────────────────────────────────────────────────────────

def load_credentials() -> dict:
    if not SECRETS_FILE.exists():
        print(f"ERROR: Secrets file not found: {SECRETS_FILE}")
        sys.exit(1)
    creds = {}
    for line in SECRETS_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            creds[key.strip()] = value.strip()
    required = ["METRICOOL_USER_TOKEN", "METRICOOL_USER_ID", "METRICOOL_BLOG_ID"]
    missing = [k for k in required if k not in creds]
    if missing:
        print(f"ERROR: Missing credentials: {missing}")
        sys.exit(1)
    return creds


# ─── Image Cache ───────────────────────────────────────────────────────────────

def load_image_cache() -> dict:
    if IMAGE_CACHE.exists():
        try:
            return json.loads(IMAGE_CACHE.read_text())
        except Exception:
            pass
    return {}


def save_image_cache(cache: dict):
    IMAGE_CACHE.write_text(json.dumps(cache, indent=2))


def upload_imgur(image_path: Path) -> str | None:
    cache = load_image_cache()
    cache_key = f"{image_path.name}:{image_path.stat().st_size}"
    if cache_key in cache:
        print(f"    📋 Cached: {image_path.name} → {cache[cache_key]}")
        return cache[cache_key]
    print(f"    📤 Uploading to Imgur: {image_path.name}...")
    try:
        b64 = base64.b64encode(image_path.read_bytes()).decode()
        resp = requests.post(
            "https://api.imgur.com/3/image",
            headers={"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"},
            data={"image": b64, "type": "base64"},
            timeout=30,
        )
        if resp.status_code == 200:
            url = resp.json().get("data", {}).get("link")
            if url:
                print(f"    ✅ Uploaded: {url}")
                cache[cache_key] = url
                save_image_cache(cache)
                return url
        print(f"    ❌ Imgur failed: {resp.status_code}")
    except Exception as e:
        print(f"    ❌ Imgur error: {e}")
    return None


# ─── Log Helpers ───────────────────────────────────────────────────────────────

def load_log() -> list:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    return []


def save_log(log: list):
    LOG_FILE.write_text(json.dumps(log, indent=2))


def is_already_scheduled(log: list, date: str, time: str) -> bool:
    """Check if a post for this date+time is already successfully logged."""
    for entry in log:
        if (entry.get("date") == date
                and entry.get("time") == time
                and entry.get("result", {}).get("success")):
            return True
    return False


# ─── Post ──────────────────────────────────────────────────────────────────────

def schedule_post(post: dict, creds: dict, dry_run: bool = False) -> dict:
    date    = post["date"]
    time_uk = post["time"]
    text    = post["text"]
    image_name = post.get("image")

    dt_iso = f"{date}T{time_uk}:00"
    channels_label = "twitter, instagram, linkedin, tiktok"

    # Resolve image
    media_urls = []
    if image_name and not dry_run:
        img_path = IMAGE_DIR / image_name
        if img_path.exists():
            url = upload_imgur(img_path)
            if url:
                media_urls.append(url)
        else:
            print(f"    ⚠️  Image not found: {img_path}")

    # Build payload
    payload = {
        "text": text,
        "publicationDate": {"dateTime": dt_iso, "timezone": TIMEZONE},
        "providers": ALL_CHANNELS,
        "autoPublish": True,
    }
    if media_urls:
        payload["media"] = media_urls

    if dry_run:
        print(f"  [DRY RUN] {date} {time_uk} UK → {channels_label}")
        print(f"            Image: {image_name or 'none'}")
        print(f"            Text: {text[:80]}...")
        return {"success": True, "dry_run": True}

    token   = creds["METRICOOL_USER_TOKEN"]
    user_id = creds["METRICOOL_USER_ID"]
    blog_id = creds["METRICOOL_BLOG_ID"]

    resp = requests.post(
        f"{BASE_URL}/v2/scheduler/posts",
        headers={"X-Mc-Auth": token, "Content-Type": "application/json"},
        params={"blogId": blog_id, "userId": user_id},
        json=payload,
        timeout=30,
    )

    result = {"status_code": resp.status_code}
    try:
        result["response"] = resp.json()
    except Exception:
        result["response"] = resp.text

    if resp.status_code in (200, 201):
        data = result["response"].get("data", {}) if isinstance(result["response"], dict) else {}
        post_id = data.get("id")
        result["success"] = True
        result["post_id"] = post_id
        print(f"  ✅ {date} {time_uk} UK — scheduled! ID: {post_id} | Image: {image_name or 'none'}")
    else:
        result["success"] = False
        print(f"  ❌ {date} {time_uk} UK — FAILED {resp.status_code}: {str(result['response'])[:200]}")

    return result


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Schedule all MTD campaign posts via Metricool API")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    parser.add_argument("--date", help="Schedule only this date (YYYY-MM-DD)")
    args = parser.parse_args()

    creds = load_credentials()
    log   = load_log()

    # Filter schedule
    posts_to_run = SCHEDULE
    if args.date:
        posts_to_run = [p for p in SCHEDULE if p["date"] == args.date]
        if not posts_to_run:
            print(f"No posts found for date: {args.date}")
            sys.exit(0)

    total   = len(posts_to_run)
    skipped = 0
    success = 0
    failed  = 0

    print(f"\n{'='*60}")
    print(f"  Genius Tax MTD — Metricool Bulk Scheduler")
    print(f"  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Posts to process: {total}")
    print(f"  Channels: Twitter, Instagram, LinkedIn, TikTok")
    print(f"{'='*60}\n")

    for post in posts_to_run:
        date    = post["date"]
        time_uk = post["time"]

        # Idempotency check
        if not args.dry_run and is_already_scheduled(log, date, time_uk):
            print(f"  ⏭️  {date} {time_uk} — already scheduled, skipping")
            skipped += 1
            continue

        result = schedule_post(post, creds, dry_run=args.dry_run)

        if not args.dry_run:
            log_entry = {
                "logged_at": datetime.now(timezone.utc).isoformat(),
                "date": date,
                "time": time_uk,
                "image": post.get("image"),
                "text_preview": post["text"][:100],
                "channels": ["twitter", "instagram", "linkedin", "tiktok"],
                "result": result,
            }
            log.append(log_entry)
            save_log(log)

        if result.get("success"):
            success += 1
        else:
            failed += 1

        # Small delay between API calls to be polite
        if not args.dry_run:
            time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  DONE")
    print(f"  Scheduled: {success}")
    print(f"  Skipped (already done): {skipped}")
    print(f"  Failed: {failed}")
    print(f"  Log: {LOG_FILE}")
    print(f"{'='*60}\n")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
