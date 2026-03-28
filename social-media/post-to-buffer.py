#!/usr/bin/env python3
"""
post-to-buffer.py — Buffer API posting script for Genius Tax
Posts content to social media via Buffer. Supports text + image posts.

Usage:
  python3 post-to-buffer.py --list-profiles
  python3 post-to-buffer.py --post "text" --channels linkedin,twitter
  python3 post-to-buffer.py --post "text" --image /path/to/image.png --channels all
  python3 post-to-buffer.py --post "text" --schedule "2026-03-26 09:00" --tz "Europe/London" --channels linkedin
  python3 post-to-buffer.py --queue-week [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# ─── Paths ────────────────────────────────────────────────────────────────────
HOME = Path.home()
SECRETS_FILE  = HOME / ".openclaw/secrets/buffer.env"
PROJECT_ROOT  = HOME / "Projects/genius-tax/social-media"
PROFILES_FILE = PROJECT_ROOT / "data/buffer-profiles.json"
LOG_FILE      = PROJECT_ROOT / "data/buffer-post-log.json"
CALENDAR_FILE = PROJECT_ROOT / "content-calendar.md"
BRANDED_DIR   = PROJECT_ROOT / "images/branded"

# ─── Buffer API ───────────────────────────────────────────────────────────────
BASE_URL = "https://api.bufferapp.com/1"

# Rate limiting — Buffer's documented limit is 60 req/min per token
# We stay well under with a modest delay between posts
POST_DELAY_SECONDS = 2

# ─── Channel → service name mapping ──────────────────────────────────────────
CHANNEL_SERVICE_MAP = {
    "linkedin":  "linkedin",
    "instagram": "instagram",
    "twitter":   "twitter",
    "x":         "twitter",
}

# ─── Branded image hints (maps content keywords → image filenames) ─────────────
IMAGE_HINTS = {
    "steps":     "branded-steps-square.png",
    "pricing":   "branded-pricing-square.png",
    "faq":       "branded-faq-story.png",
    "hero":      "branded-hero-square.png",
    "linkedin":  "branded-hero-linkedin.png",
    "plan":      "branded-pricing-square.png",
    "sorted":    "01-your-tax-sorted.png",
    "simple":    "04-simple-pricing.png",
    "questions": "05-questions-story.png",
    "pick":      "06-pick-your-plan.png",
}

# ─── X schedule times (UK local) ─────────────────────────────────────────────
X_TIMES       = ["08:00", "11:30", "16:30"]
LINKEDIN_TIMES = ["09:00", "12:00", "16:00"]
UK_TZ         = ZoneInfo("Europe/London")


# ══════════════════════════════════════════════════════════════════════════════
# Auth / token helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_token() -> str:
    """Read BUFFER_ACCESS_TOKEN from secrets file."""
    if not SECRETS_FILE.exists():
        die(
            f"Token file not found: {SECRETS_FILE}\n"
            "Create it with:\n"
            "  echo 'BUFFER_ACCESS_TOKEN=your_token_here' > ~/.openclaw/secrets/buffer.env"
        )
    for line in SECRETS_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("BUFFER_ACCESS_TOKEN="):
            token = line.split("=", 1)[1].strip()
            if token:
                return token
    die("BUFFER_ACCESS_TOKEN not found in secrets file.")


def die(msg: str, code: int = 1) -> None:
    print(f"❌  {msg}", file=sys.stderr)
    sys.exit(code)


# ══════════════════════════════════════════════════════════════════════════════
# Buffer API wrappers
# ══════════════════════════════════════════════════════════════════════════════

def api_get(path: str, token: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}/{path}"
    p = {"access_token": token}
    if params:
        p.update(params)
    r = requests.get(url, params=p, timeout=15)
    _check(r)
    return r.json()


def api_post(path: str, token: str, data: dict) -> dict:
    url = f"{BASE_URL}/{path}"
    data["access_token"] = token
    r = requests.post(url, data=data, timeout=15)
    _check(r)
    return r.json()


def _check(r: requests.Response) -> None:
    if r.status_code == 429:
        die("Rate limited by Buffer. Wait a minute and try again.")
    if not r.ok:
        try:
            msg = r.json().get("error", r.text)
        except Exception:
            msg = r.text
        die(f"Buffer API error {r.status_code}: {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# Profile management
# ══════════════════════════════════════════════════════════════════════════════

def fetch_profiles(token: str) -> list[dict]:
    """Fetch profiles from Buffer and cache locally."""
    print("🔄  Fetching profiles from Buffer…")
    raw = api_get("profiles.json", token)
    profiles = []
    for p in raw:
        profiles.append({
            "id":           p["id"],
            "service":      p["service"],
            "service_username": p.get("service_username", ""),
            "formatted_username": p.get("formatted_username", ""),
        })
    PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2))
    print(f"✅  Cached {len(profiles)} profile(s) → {PROFILES_FILE}")
    return profiles


def load_profiles(token: str) -> list[dict]:
    """Return cached profiles, refreshing if cache is absent."""
    if PROFILES_FILE.exists():
        return json.loads(PROFILES_FILE.read_text())
    return fetch_profiles(token)


def resolve_channels(channels_arg: str, profiles: list[dict]) -> list[dict]:
    """Return the subset of profiles matching the requested channels."""
    if channels_arg.lower() == "all":
        return profiles

    requested = [c.strip().lower() for c in channels_arg.split(",")]
    selected = []
    for ch in requested:
        svc = CHANNEL_SERVICE_MAP.get(ch, ch)
        matches = [p for p in profiles if p["service"] == svc]
        if not matches:
            print(f"⚠️   No profile found for channel '{ch}' (service='{svc}')")
        selected.extend(matches)

    # de-duplicate by id
    seen = set()
    out = []
    for p in selected:
        if p["id"] not in seen:
            seen.add(p["id"])
            out.append(p)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# Posting
# ══════════════════════════════════════════════════════════════════════════════

def build_post_data(
    profile_ids: list[str],
    text: str,
    image_url: str | None = None,
    scheduled_at: int | None = None,
    now: bool = False,
) -> dict:
    data: dict = {"text": text}
    for pid in profile_ids:
        data.setdefault("profile_ids[]", [])
        if isinstance(data["profile_ids[]"], str):
            data["profile_ids[]"] = [data["profile_ids[]"]]
        data["profile_ids[]"] = profile_ids  # Buffer accepts list via repeat key

    if image_url:
        data["media[photo]"] = image_url
        data["media[thumbnail]"] = image_url
    if scheduled_at:
        data["scheduled_at"] = scheduled_at
    if now:
        data["now"] = "true"
    return data


def post_update(
    token: str,
    profiles: list[dict],
    text: str,
    image_url: str | None,
    scheduled_at: int | None,
    now: bool,
    dry_run: bool,
) -> dict | None:
    """Create a Buffer update. Returns API response or None (dry-run)."""
    profile_ids = [p["id"] for p in profiles]

    # Build flat form-encoded data — Buffer requires repeated keys for arrays
    post_data = {
        "text": text,
        "access_token": token,
    }
    # Requests handles list values as repeated keys automatically
    post_data["profile_ids[]"] = profile_ids
    if image_url:
        post_data["media[photo]"] = image_url
        post_data["media[thumbnail]"] = image_url
    if scheduled_at:
        post_data["scheduled_at"] = scheduled_at
    if now:
        post_data["now"] = "true"

    if dry_run:
        return None

    url = f"{BASE_URL}/updates/create.json"
    r = requests.post(url, data=post_data, timeout=15)
    _check(r)
    return r.json()


def log_post(entry: dict) -> None:
    """Append a post entry to the JSON log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text())
        except Exception:
            log = []
    log.append(entry)
    LOG_FILE.write_text(json.dumps(log, indent=2))


# ══════════════════════════════════════════════════════════════════════════════
# Image helpers
# ══════════════════════════════════════════════════════════════════════════════

def resolve_image(image_arg: str | None) -> str | None:
    """
    Accept a URL or local path. Warns if local — Buffer needs a URL.
    Returns None if no image provided.
    """
    if not image_arg:
        return None
    if image_arg.startswith("http://") or image_arg.startswith("https://"):
        return image_arg
    path = Path(image_arg).expanduser()
    if not path.exists():
        print(f"⚠️   Image file not found: {path}")
        return None
    print(
        f"⚠️   Local image path given: {path}\n"
        "     Buffer requires a publicly accessible URL for media[photo].\n"
        "     Upload the image somewhere (e.g., Cloudinary, S3, or Buffer's media endpoint)\n"
        "     and pass the URL instead. Skipping image for this post."
    )
    return None


def pick_branded_image(text: str) -> str | None:
    """Heuristically pick a branded image based on post text keywords."""
    text_lower = text.lower()
    for keyword, filename in IMAGE_HINTS.items():
        if keyword in text_lower:
            candidate = BRANDED_DIR / filename
            if candidate.exists():
                return str(candidate)
    # Fallback to hero image
    fallback = BRANDED_DIR / "branded-hero-square.png"
    if fallback.exists():
        return str(fallback)
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Schedule helpers
# ══════════════════════════════════════════════════════════════════════════════

def parse_schedule(schedule_str: str, tz_name: str) -> int:
    """Parse 'YYYY-MM-DD HH:MM' in given timezone, return Unix timestamp."""
    tz = ZoneInfo(tz_name)
    dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    return int(dt.timestamp())


def uk_datetime_to_ts(date: datetime.date, time_str: str) -> int:
    """Convert a date + 'HH:MM' UK time string to a Unix timestamp."""
    h, m = map(int, time_str.split(":"))
    dt = datetime(date.year, date.month, date.day, h, m, tzinfo=UK_TZ)
    return int(dt.timestamp())


# ══════════════════════════════════════════════════════════════════════════════
# Content calendar parser
# ══════════════════════════════════════════════════════════════════════════════

def parse_calendar(calendar_text: str) -> dict[str, dict]:
    """
    Parse the content-calendar.md and return a dict:
      { "2026-03-24": { "x": ["morning text", "afternoon text", "evening text"],
                        "linkedin": "linkedin text",
                        "instagram": ["post1", "post2"] } }
    """
    # Find day sections (e.g. ## MARCH 24, 2026 ...)
    day_pattern = re.compile(
        r"^## ([A-Z]+ \d+, \d{4})",
        re.MULTILINE,
    )
    sections = day_pattern.split(calendar_text)

    # sections[0] = preamble, then pairs: (date_str, content)
    result = {}
    months = {
        "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
        "MAY": 5, "JUNE": 6, "JULY": 7, "AUGUST": 8,
        "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
    }

    i = 1
    while i < len(sections) - 1:
        date_str = sections[i].strip()
        content  = sections[i + 1]
        i += 2

        # Parse date
        m = re.match(r"([A-Z]+)\s+(\d+),\s+(\d{4})", date_str)
        if not m:
            continue
        month_name, day, year = m.groups()
        month_num = months.get(month_name)
        if not month_num:
            continue
        iso_date = f"{year}-{month_num:02d}-{int(day):02d}"

        day_data: dict = {}

        # ── X / Twitter posts ──────────────────────────────────────────────
        x_match = re.search(
            r"### X/Twitter\s*(.*?)(?=###|\Z)", content, re.DOTALL
        )
        if x_match:
            x_section = x_match.group(1)
            morning   = _extract_section(x_section, "Morning")
            afternoon = _extract_section(x_section, "Afternoon")
            evening   = _extract_section(x_section, "Evening")
            x_posts = [p for p in [morning, afternoon, evening] if p]
            if x_posts:
                day_data["x"] = x_posts

        # ── LinkedIn ──────────────────────────────────────────────────────
        li_match = re.search(
            r"### LinkedIn\s*(.*?)(?=###|\Z)", content, re.DOTALL
        )
        if li_match:
            li_text = li_match.group(1).strip()
            if li_text:
                day_data["linkedin"] = li_text

        # ── Instagram ────────────────────────────────────────────────────
        ig_match = re.search(
            r"### Instagram\s*(.*?)(?=###|\Z)", content, re.DOTALL
        )
        if ig_match:
            ig_section = ig_match.group(1)
            post1 = _extract_section(ig_section, "Post 1")
            post2 = _extract_section(ig_section, "Post 2")
            ig_posts = [p for p in [post1, post2] if p]
            if ig_posts:
                day_data["instagram"] = ig_posts

        if day_data:
            result[iso_date] = day_data

    return result


def _extract_section(text: str, label: str) -> str | None:
    """Extract text under a bold label like **Morning:** until next ** or end."""
    pattern = rf"\*\*{re.escape(label)}[:\s]*\*\*\s*(.*?)(?=\*\*|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Commands
# ══════════════════════════════════════════════════════════════════════════════

def cmd_list_profiles(token: str) -> None:
    """Fetch (and cache) profiles, print them."""
    profiles = fetch_profiles(token)
    print(f"\n{'─'*60}")
    print(f"  {'SERVICE':<15} {'USERNAME':<25} {'ID'}")
    print(f"{'─'*60}")
    for p in profiles:
        name = p.get("formatted_username") or p.get("service_username") or "—"
        print(f"  {p['service']:<15} {name:<25} {p['id']}")
    print(f"{'─'*60}\n")


def cmd_post(
    token: str,
    text: str,
    channels: str,
    image_arg: str | None,
    schedule_str: str | None,
    tz_name: str,
    now: bool,
    dry_run: bool,
) -> None:
    profiles = load_profiles(token)
    targets = resolve_channels(channels, profiles)
    if not targets:
        die("No matching profiles found. Run --list-profiles to see what's connected.")

    image_url = resolve_image(image_arg)

    scheduled_at = None
    if schedule_str:
        scheduled_at = parse_schedule(schedule_str, tz_name)
        sched_label = datetime.fromtimestamp(scheduled_at).strftime("%Y-%m-%d %H:%M %Z")
    else:
        sched_label = "queued (next slot)" if not now else "now"

    print(f"\n{'─'*60}")
    print(f"  📤  Posting to {len(targets)} channel(s)")
    for p in targets:
        name = p.get("formatted_username") or p.get("service_username") or p["id"]
        print(f"       • {p['service']}: {name}")
    print(f"  📝  Text   : {text[:80]}{'…' if len(text) > 80 else ''}")
    print(f"  🖼️   Image  : {image_url or 'none'}")
    print(f"  🕒  When   : {sched_label}")
    if dry_run:
        print("  🧪  DRY RUN — nothing was posted")
    print(f"{'─'*60}\n")

    if dry_run:
        return

    resp = post_update(
        token=token,
        profiles=targets,
        text=text,
        image_url=image_url,
        scheduled_at=scheduled_at,
        now=now,
        dry_run=False,
    )

    log_post({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "channels":  [p["service"] for p in targets],
        "profile_ids": [p["id"] for p in targets],
        "text":      text,
        "image_url": image_url,
        "scheduled_at": scheduled_at,
        "buffer_response": resp,
    })

    if resp and resp.get("success"):
        print(f"✅  Posted successfully!")
    elif resp:
        print(f"⚠️   Buffer returned: {resp}")


def cmd_queue_week(token: str, dry_run: bool) -> None:
    """Parse content calendar and queue the next 7 days."""
    if not CALENDAR_FILE.exists():
        die(f"Content calendar not found: {CALENDAR_FILE}")

    calendar_text = CALENDAR_FILE.read_text()
    calendar      = parse_calendar(calendar_text)
    profiles      = load_profiles(token)

    today = datetime.now(tz=UK_TZ).date()
    end   = today + timedelta(days=7)

    queued = 0
    skipped = 0
    summary: list[str] = []

    print(f"\n📅  Queueing content for {today} → {end - timedelta(days=1)} (UK time)\n")

    # Sort dates ascending
    for iso_date, day_data in sorted(calendar.items()):
        date = datetime.strptime(iso_date, "%Y-%m-%d").date()
        if not (today <= date < end):
            continue

        print(f"  📆  {iso_date}")

        # ── X posts ───────────────────────────────────────────────────────
        x_posts = day_data.get("x", [])
        x_profiles = [p for p in profiles if p["service"] == "twitter"]
        for idx, post_text in enumerate(x_posts[:3]):
            time_str = X_TIMES[idx] if idx < len(X_TIMES) else X_TIMES[-1]
            ts = uk_datetime_to_ts(date, time_str)
            img_path = pick_branded_image(post_text)
            img_url  = None  # local paths need URL hosting; warn only

            if img_path:
                print(
                    f"     ℹ️  X post has a branded image suggestion ({Path(img_path).name}),\n"
                    f"        but Buffer needs a URL. Posting text-only for now."
                )

            label = ["Morning", "Afternoon", "Evening"][idx]
            print(f"     🐦  X {label} @ {time_str} UK: {post_text[:60]}…")

            if x_profiles and not dry_run:
                resp = post_update(token, x_profiles, post_text, img_url, ts, False, False)
                log_post({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "date": iso_date,
                    "slot": label,
                    "channels": ["twitter"],
                    "profile_ids": [p["id"] for p in x_profiles],
                    "text": post_text,
                    "image_url": img_url,
                    "scheduled_at": ts,
                    "buffer_response": resp,
                })
                queued += 1
                time.sleep(POST_DELAY_SECONDS)
            elif not x_profiles:
                print("       ⚠️  No Twitter/X profile connected — skipping")
                skipped += 1
            else:
                queued += 1  # dry run count

            summary.append(f"[{iso_date}] X {label}: {post_text[:50]}…")

        # ── LinkedIn posts ────────────────────────────────────────────────
        li_text = day_data.get("linkedin")
        li_profiles = [p for p in profiles if p["service"] == "linkedin"]
        if li_text:
            for slot_idx, time_str in enumerate(LINKEDIN_TIMES[:1]):  # 1 post/day for LinkedIn
                ts = uk_datetime_to_ts(date, time_str)
                img_path = pick_branded_image(li_text)
                img_url  = None  # same URL caveat

                if img_path:
                    print(
                        f"     ℹ️  LinkedIn post has branded image suggestion ({Path(img_path).name}),\n"
                        f"        Buffer needs a URL — posting text-only."
                    )

                print(f"     💼  LinkedIn @ {time_str} UK: {li_text[:60]}…")

                if li_profiles and not dry_run:
                    resp = post_update(token, li_profiles, li_text, img_url, ts, False, False)
                    log_post({
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "date": iso_date,
                        "slot": f"LinkedIn {time_str}",
                        "channels": ["linkedin"],
                        "profile_ids": [p["id"] for p in li_profiles],
                        "text": li_text,
                        "image_url": img_url,
                        "scheduled_at": ts,
                        "buffer_response": resp,
                    })
                    queued += 1
                    time.sleep(POST_DELAY_SECONDS)
                elif not li_profiles:
                    print("       ⚠️  No LinkedIn profile connected — skipping")
                    skipped += 1
                else:
                    queued += 1  # dry run

            summary.append(f"[{iso_date}] LinkedIn: {li_text[:50]}…")

        # ── Instagram posts ───────────────────────────────────────────────
        ig_posts = day_data.get("instagram", [])
        ig_profiles = [p for p in profiles if p["service"] == "instagram"]
        for idx, post_text in enumerate(ig_posts[:2]):
            time_str = "10:00" if idx == 0 else "18:00"
            ts = uk_datetime_to_ts(date, time_str)
            print(f"     📸  Instagram Post {idx+1} @ {time_str} UK: {post_text[:60]}…")

            if ig_profiles and not dry_run:
                resp = post_update(token, ig_profiles, post_text, None, ts, False, False)
                log_post({
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "date": iso_date,
                    "slot": f"Instagram {idx+1}",
                    "channels": ["instagram"],
                    "profile_ids": [p["id"] for p in ig_profiles],
                    "text": post_text,
                    "image_url": None,
                    "scheduled_at": ts,
                    "buffer_response": resp,
                })
                queued += 1
                time.sleep(POST_DELAY_SECONDS)
            elif not ig_profiles:
                print("       ⚠️  No Instagram profile connected — skipping")
                skipped += 1
            else:
                queued += 1

            summary.append(f"[{iso_date}] Instagram {idx+1}: {post_text[:50]}…")

        print()

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"{'─'*60}")
    if dry_run:
        print(f"  🧪  DRY RUN complete — {queued} post(s) would be queued, {skipped} skipped")
    else:
        print(f"  ✅  Done — {queued} post(s) queued, {skipped} skipped")
    print(f"{'─'*60}")
    print("\nSummary:")
    for line in summary:
        print(f"  {line}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# CLI entry point
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post content to social media via Buffer API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Mutually exclusive main commands
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list-profiles",
        action="store_true",
        help="Fetch and display connected Buffer profiles",
    )
    group.add_argument(
        "--post",
        metavar="TEXT",
        help="Post this text to the specified channels",
    )
    group.add_argument(
        "--queue-week",
        action="store_true",
        help="Queue next 7 days from content-calendar.md",
    )

    # --post options
    parser.add_argument(
        "--channels",
        metavar="CHANNELS",
        default="all",
        help="Comma-separated: linkedin,instagram,twitter,x — or 'all'",
    )
    parser.add_argument(
        "--image",
        metavar="PATH_OR_URL",
        help="Image to attach (URL or local path — Buffer requires a URL)",
    )
    parser.add_argument(
        "--schedule",
        metavar="DATETIME",
        help="Schedule time as 'YYYY-MM-DD HH:MM'",
    )
    parser.add_argument(
        "--tz",
        metavar="TIMEZONE",
        default="Europe/London",
        help="Timezone for --schedule (default: Europe/London)",
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="Post immediately instead of adding to queue",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be posted without actually posting",
    )
    parser.add_argument(
        "--refresh-profiles",
        action="store_true",
        help="Force re-fetch of profiles from Buffer (clears cache)",
    )

    args = parser.parse_args()

    # Load token (graceful failure if missing)
    try:
        token = load_token()
    except SystemExit:
        if args.list_profiles or args.post or args.queue_week:
            raise
        token = ""

    # Force profile refresh if requested
    if args.refresh_profiles and PROFILES_FILE.exists():
        PROFILES_FILE.unlink()
        print("🗑️   Profile cache cleared.")

    # ── Route commands ─────────────────────────────────────────────────────
    if args.list_profiles:
        cmd_list_profiles(token)

    elif args.post:
        cmd_post(
            token=token,
            text=args.post,
            channels=args.channels,
            image_arg=args.image,
            schedule_str=args.schedule,
            tz_name=args.tz,
            now=args.now,
            dry_run=args.dry_run,
        )

    elif args.queue_week:
        cmd_queue_week(token, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
