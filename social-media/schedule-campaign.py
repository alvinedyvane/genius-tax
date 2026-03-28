#!/usr/bin/env python3
"""
schedule-campaign.py
Schedules the Genius Tax MTD campaign posts across specific dates via Metricool.

Usage:
  python3 schedule-campaign.py [--dry-run]

Dates covered:
  2026-03-26, 2026-03-27, 2026-03-30, 2026-03-31,
  2026-04-01, 2026-04-02, 2026-04-03
"""

import argparse
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# ─── Config ───────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent

CAMPAIGN_DATES = [
    "2026-03-26",
    "2026-03-27",
    "2026-03-30",
    "2026-03-31",
    "2026-04-01",
    "2026-04-02",
    "2026-04-03",
]

# Times in UK (Europe/London) — use max 2 per day if only 2 posts
UK_TIMES = ["09:00", "13:00", "17:00"]

BRANDED_IMAGES = [
    "01-your-tax-sorted.png",
    "02-built-for-people.png",
    "03-three-steps.png",
    "04-simple-pricing.png",
    "06-pick-your-plan.png",
    "07-ready-sorted.png",
]

CALENDAR_FILE = BASE_DIR / "content-calendar.md"
IMAGES_DIR = BASE_DIR / "images" / "branded"
POSTER_SCRIPT = BASE_DIR / "metricool-api-poster.py"

LONDON_TZ = ZoneInfo("Europe/London")

# ─── Calendar parsing ──────────────────────────────────────────────────────────

# Maps "MARCH 26, 2026" → "2026-03-26"
MONTH_MAP = {
    "JANUARY": "01", "FEBRUARY": "02", "MARCH": "03", "APRIL": "04",
    "MAY": "05", "JUNE": "06", "JULY": "07", "AUGUST": "08",
    "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11", "DECEMBER": "12",
}


def parse_calendar_date(header: str) -> str | None:
    """Parse '## MARCH 26, 2026 — ...' into 'YYYY-MM-DD'."""
    m = re.search(r"##\s+([A-Z]+)\s+(\d+),\s+(\d{4})", header)
    if not m:
        return None
    month_name, day, year = m.group(1), m.group(2), m.group(3)
    month = MONTH_MAP.get(month_name.upper())
    if not month:
        return None
    return f"{year}-{month}-{int(day):02d}"


def extract_instagram_posts(calendar_text: str, target_date: str) -> list[str]:
    """
    Find the section for target_date and extract all Instagram **Post N:** blocks.
    Returns a list of post texts (stripped).
    """
    lines = calendar_text.splitlines()
    posts = []

    # Find the line index for our target date section
    section_start = None
    section_end = None

    for i, line in enumerate(lines):
        if line.startswith("## "):
            parsed = parse_calendar_date(line)
            if parsed == target_date:
                section_start = i
            elif section_start is not None:
                # We've moved past our section
                section_end = i
                break

    if section_start is None:
        return []

    if section_end is None:
        section_end = len(lines)

    section_lines = lines[section_start:section_end]

    # Find ### Instagram subsection within the date section
    ig_start = None
    ig_end = None
    for i, line in enumerate(section_lines):
        if line.strip() == "### Instagram":
            ig_start = i + 1
        elif ig_start is not None and line.startswith("### "):
            ig_end = i
            break

    if ig_start is None:
        return []
    if ig_end is None:
        ig_end = len(section_lines)

    ig_lines = section_lines[ig_start:ig_end]
    ig_text = "\n".join(ig_lines)

    # Extract post blocks: **Post N:** ... until next **Post or end
    # Pattern: **Post 1:** followed by content until **Post 2:** or end
    post_pattern = re.compile(r'\*\*Post \d+:\*\*\s*\n(.*?)(?=\*\*Post \d+:\*\*|\Z)', re.DOTALL)
    matches = post_pattern.findall(ig_text)

    for match in matches:
        text = match.strip()
        # Remove any trailing "---" separators
        text = re.sub(r'\n---\s*$', '', text).strip()
        if text:
            posts.append(text)

    return posts


# ─── Scheduling logic ──────────────────────────────────────────────────────────

def is_past(date_str: str, time_str: str) -> bool:
    """Return True if the given date+time (Europe/London) is in the past vs UTC now."""
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    london_dt = naive_dt.replace(tzinfo=LONDON_TZ)
    now_utc = datetime.now(timezone.utc)
    return london_dt < now_utc


def schedule_post(post_text: str, image_path: Path, schedule_dt: str, dry_run: bool) -> bool:
    """
    Call metricool-api-poster.py to schedule a single post via REST API.
    Returns True on success, False on failure.
    Retries once after 10s if the first attempt fails.
    """
    cmd = [
        sys.executable,
        str(POSTER_SCRIPT),
        "--text", post_text,
        "--image", str(image_path),
        "--channels", "facebook,instagram",
        "--schedule", schedule_dt,
    ]

    if dry_run:
        print(f"    [DRY RUN] Would run: python3 metricool-poster.py \\")
        print(f"      --post \"[{len(post_text)} chars]\" \\")
        print(f"      --image {image_path.name} \\")
        print(f"      --channels instagram,facebook \\")
        print(f"      --schedule \"{schedule_dt}\" --tz Europe/London")
        return True

    for attempt in range(1, 3):
        print(f"    [Attempt {attempt}] Scheduling post for {schedule_dt}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    ✅ Success")
            if result.stdout.strip():
                print(f"    {result.stdout.strip()[:200]}")
            return True
        else:
            print(f"    ❌ Failed (exit {result.returncode})")
            if result.stderr.strip():
                print(f"    STDERR: {result.stderr.strip()[:300]}")
            if result.stdout.strip():
                print(f"    STDOUT: {result.stdout.strip()[:300]}")
            if attempt < 2:
                print(f"    Retrying in 10 seconds...")
                time.sleep(10)

    return False


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Schedule Genius Tax MTD campaign posts")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be scheduled without posting")
    args = parser.parse_args()

    dry_run = args.dry_run

    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE — no posts will be submitted")
        print("=" * 60)

    # Load calendar
    if not CALENDAR_FILE.exists():
        print(f"ERROR: content-calendar.md not found at {CALENDAR_FILE}")
        sys.exit(1)

    calendar_text = CALENDAR_FILE.read_text(encoding="utf-8")

    # Track summary
    scheduled_count = 0
    skipped_past = 0
    failed_count = 0
    scheduled_summary = []  # [(date, time, post_num)]
    skipped_dates = []

    # Global image rotation index (resets per day as per spec)
    for date_str in CAMPAIGN_DATES:
        print(f"\n{'='*60}")
        print(f"📅 Processing: {date_str}")

        # Extract posts for this date
        posts = extract_instagram_posts(calendar_text, date_str)

        if not posts:
            print(f"  ⚠️  No Instagram posts found for {date_str} — skipping")
            continue

        print(f"  Found {len(posts)} Instagram post(s)")

        # Use max 2 posts if only 2 exist (or fewer times)
        times_to_use = UK_TIMES[:len(posts)]  # up to 3 but bounded by post count

        # Image rotation resets each day
        day_images = BRANDED_IMAGES.copy()  # rotate from start each day

        day_scheduled = []
        day_skipped = []

        for post_idx, (post_text, time_str) in enumerate(zip(posts, times_to_use)):
            schedule_dt = f"{date_str} {time_str}"

            if is_past(date_str, time_str):
                print(f"  ⏭️  {schedule_dt} UK — IN THE PAST, skipping")
                day_skipped.append(time_str)
                skipped_past += 1
                continue

            # Pick image (rotate through branded list, resetting each day)
            image_name = day_images[post_idx % len(day_images)]
            image_path = IMAGES_DIR / image_name

            if not image_path.exists():
                print(f"  ⚠️  Image not found: {image_path} — skipping")
                continue

            print(f"\n  📸 Post {post_idx+1} → {schedule_dt} UK | Image: {image_name}")
            print(f"     Text preview: {post_text[:80].replace(chr(10), ' ')}...")

            success = schedule_post(post_text, image_path, schedule_dt, dry_run)

            if success:
                scheduled_count += 1
                day_scheduled.append(time_str)
                scheduled_summary.append((date_str, time_str, post_idx + 1))
            else:
                failed_count += 1

            # Pause between posts to avoid hammering Metricool
            if not dry_run and post_idx < len(posts) - 1:
                print(f"  ⏳ Pausing 5s before next post...")
                time.sleep(5)

        if day_skipped and not day_scheduled:
            skipped_dates.append(date_str)

    # ─── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("📊 CAMPAIGN SCHEDULE SUMMARY")
    print(f"{'='*60}")

    if dry_run:
        print("⚠️  DRY RUN — nothing was actually posted\n")

    print(f"✅ Posts {'would be ' if dry_run else ''}scheduled: {scheduled_count}")
    print(f"⏭️  Skipped (past):   {skipped_past}")
    print(f"❌ Failed:           {failed_count}")

    if scheduled_summary:
        print(f"\nSchedule:")
        current_date = None
        for date_str, time_str, post_num in scheduled_summary:
            if date_str != current_date:
                print(f"  {date_str}:")
                current_date = date_str
            print(f"    • {time_str} UK — Post {post_num}")

    if skipped_dates:
        print(f"\nFully skipped dates (all times in past):")
        for d in skipped_dates:
            print(f"  • {d}")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
