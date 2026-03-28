#!/usr/bin/env python3
"""
Genius Tax — Social Media Monitor
Checks X/Twitter mentions and LinkedIn comments, auto-responds to common queries,
likes positives, and flags complex/negative content for manual review.

Usage:
  python3 monitor.py [--once] [--interval 900] [--dry-run]
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests_oauthlib import OAuth1

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SECRETS_DIR = Path.home() / ".openclaw" / "secrets"

STATE_FILE   = DATA_DIR / "monitor-state.json"
LOG_FILE     = DATA_DIR / "monitor-log.json"
FLAGGED_FILE = DATA_DIR / "flagged-for-review.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("genius-monitor")

# ─────────────────────────────────────────────
# RESPONSE TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = {
    "pricing": (
        "Great question! Essential starts at £199 upfront, Growth early bird is £299 upfront "
        "(ends April 5). Full details at geniustax.co.uk"
    ),
    "mtd": (
        "MTD (Making Tax Digital) requires quarterly digital reporting to HMRC from "
        "April 6, 2026 for self-employed/landlords earning over £50K. We handle "
        "everything for you — geniustax.co.uk"
    ),
    "signup": (
        "Takes 3 minutes! Head to geniustax.co.uk and pick your plan. "
        "We'll have you set up within 48 hours."
    ),
    "interest": (
        "Thanks for your interest! Check out geniustax.co.uk or DM us for a chat."
    ),
}

# Keywords that map to each template
KEYWORD_MAP = {
    "pricing": [
        "price", "pricing", "cost", "how much", "£", "fee", "fees",
        "plan", "plans", "essential", "growth", "subscription",
    ],
    "mtd": [
        "mtd", "making tax digital", "quarterly", "digital reporting",
        "hmrc", "self-employed", "landlord", "self employed",
    ],
    "signup": [
        "sign up", "signup", "join", "register", "how do i start",
        "get started", "onboard",
    ],
}

NEGATIVE_SIGNALS = [
    "terrible", "awful", "scam", "fraud", "useless", "hate", "worst",
    "rubbish", "garbage", "bad", "complaint", "refund", "money back",
    "stolen", "ripped off", "rip off", "disappointed", "horrible",
]

POSITIVE_SIGNALS = [
    "love", "great", "amazing", "excellent", "fantastic", "brilliant",
    "awesome", "good", "nice", "thanks", "thank you", "helpful",
    "recommend", "perfect", "👍", "❤️", "🙌", "🎉",
]

# LinkedIn URNs to monitor
LINKEDIN_SHARE_URNS = [
    "urn:li:share:7442529476200161280",
    "urn:li:share:7442529946373312512",
    "urn:li:share:7442285925449129984",
]

# ─────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────

def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            log.warning(f"Corrupt JSON at {path}, starting fresh.")
    return default


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_state() -> dict:
    return load_json(STATE_FILE, {
        "replied_tweet_ids": [],
        "liked_tweet_ids": [],
        "seen_linkedin_comment_ids": [],
        "x_reply_timestamps": [],   # ISO timestamps of replies this hour
        "last_x_mention_id": None,
        "last_run": None,
    })


def save_state(state: dict):
    save_json(STATE_FILE, state)


def append_log(entry: dict):
    entries = load_json(LOG_FILE, [])
    entries.append(entry)
    save_json(LOG_FILE, entries)


def append_flagged(entry: dict):
    entries = load_json(FLAGGED_FILE, [])
    entries.append(entry)
    save_json(FLAGGED_FILE, entries)


# ─────────────────────────────────────────────
# CREDENTIAL LOADING
# ─────────────────────────────────────────────

def load_env_file(path: Path) -> dict:
    env = {}
    if not path.exists():
        raise FileNotFoundError(f"Secrets file not found: {path}")
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def get_x_credentials() -> dict:
    env = load_env_file(SECRETS_DIR / "x-geniustax.env")
    return {
        "consumer_key":        env["X_CONSUMER_KEY"],
        "consumer_secret":     env["X_SECRET_KEY"],
        "access_token":        env["X_ACCESS_TOKEN"],
        "access_token_secret": env["X_ACCESS_TOKEN_SECRET"],
        "bearer_token":        env["X_BEARER_TOKEN"],
    }


def get_linkedin_credentials() -> dict:
    env = load_env_file(SECRETS_DIR / "linkedin-geniusmoney.env")
    return {
        "access_token": env["LINKEDIN_ACCESS_TOKEN"],
        "person_urn":   f"urn:li:person:{env['LINKEDIN_PERSON_URN']}",
    }


# ─────────────────────────────────────────────
# CLASSIFICATION
# ─────────────────────────────────────────────

def classify_text(text: str) -> str:
    """
    Returns: 'pricing' | 'mtd' | 'signup' | 'positive' | 'negative' | 'interest'
    """
    lower = text.lower()

    for signal in NEGATIVE_SIGNALS:
        if signal in lower:
            return "negative"

    for category, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in lower:
                return category

    for signal in POSITIVE_SIGNALS:
        if signal in lower:
            return "positive"

    return "interest"


def get_reply_text(category: str) -> str | None:
    """Return reply template, or None if we should just like/flag."""
    return TEMPLATES.get(category)


# ─────────────────────────────────────────────
# RATE LIMIT HELPERS
# ─────────────────────────────────────────────

def x_replies_this_hour(state: dict) -> int:
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - 3600
    recent = [
        ts for ts in state.get("x_reply_timestamps", [])
        if datetime.fromisoformat(ts).timestamp() > cutoff
    ]
    state["x_reply_timestamps"] = recent
    return len(recent)


def record_x_reply(state: dict):
    state.setdefault("x_reply_timestamps", [])
    state["x_reply_timestamps"].append(datetime.now(timezone.utc).isoformat())


# ─────────────────────────────────────────────
# X / TWITTER API
# ─────────────────────────────────────────────

def x_get(url: str, creds: dict, params: dict = None) -> dict:
    """GET with Bearer token."""
    headers = {"Authorization": f"Bearer {creds['bearer_token']}"}
    r = requests.get(url, headers=headers, params=params, timeout=15)
    if r.status_code == 429:
        log.warning("X rate limit hit — sleeping 60s")
        time.sleep(60)
        return {}
    r.raise_for_status()
    return r.json()


def x_post(url: str, creds: dict, payload: dict, dry_run: bool) -> dict:
    """POST with OAuth 1.0a."""
    if dry_run:
        log.info(f"[DRY-RUN] POST {url} — {payload}")
        return {"dry_run": True}
    auth = OAuth1(
        creds["consumer_key"],
        creds["consumer_secret"],
        creds["access_token"],
        creds["access_token_secret"],
    )
    r = requests.post(url, json=payload, auth=auth, timeout=15)
    if r.status_code == 429:
        log.warning("X rate limit hit on POST — backing off 60s")
        time.sleep(60)
    r.raise_for_status()
    return r.json()


def get_x_user_id(username: str, creds: dict) -> str:
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    data = x_get(url, creds)
    return data.get("data", {}).get("id")


def get_x_mentions(user_id: str, creds: dict, since_id: str = None) -> list:
    params = {
        "tweet.fields": "author_id,text,created_at,conversation_id,public_metrics",
        "expansions": "author_id",
        "user.fields": "username,name",
        "max_results": 10,
    }
    if since_id:
        params["since_id"] = since_id
    url = f"https://api.twitter.com/2/users/{user_id}/mentions"
    data = x_get(url, creds, params)
    return data.get("data", [])


def like_tweet(tweet_id: str, user_id: str, creds: dict, dry_run: bool):
    url = f"https://api.twitter.com/2/users/{user_id}/likes"
    return x_post(url, creds, {"tweet_id": tweet_id}, dry_run)


def reply_to_tweet(tweet_id: str, text: str, creds: dict, dry_run: bool):
    url = "https://api.twitter.com/2/tweets"
    payload = {"text": text, "reply": {"in_reply_to_tweet_id": tweet_id}}
    return x_post(url, creds, payload, dry_run)


# ─────────────────────────────────────────────
# LINKEDIN API
# ─────────────────────────────────────────────

def li_headers(creds: dict) -> dict:
    return {
        "Authorization": f"Bearer {creds['access_token']}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }


def get_linkedin_comments(share_urn: str, creds: dict) -> list:
    encoded_urn = requests.utils.quote(share_urn, safe="")
    url = f"https://api.linkedin.com/v2/socialActions/{encoded_urn}/comments"
    params = {"count": 20}
    try:
        r = requests.get(url, headers=li_headers(creds), params=params, timeout=15)
        if r.status_code == 401:
            log.warning("LinkedIn token expired or invalid.")
            return []
        if r.status_code == 403:
            log.warning(f"LinkedIn 403 for URN {share_urn} — may need org token.")
            return []
        r.raise_for_status()
        data = r.json()
        return data.get("elements", [])
    except requests.RequestException as e:
        log.error(f"LinkedIn API error for {share_urn}: {e}")
        return []


# ─────────────────────────────────────────────
# MONITORING LOGIC
# ─────────────────────────────────────────────

def monitor_x(state: dict, dry_run: bool):
    log.info("── Checking X/Twitter mentions ──")
    try:
        creds = get_x_credentials()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    # Resolve user ID (cache it in state)
    user_id = state.get("x_user_id")
    if not user_id:
        user_id = get_x_user_id("geniusmoneytax", creds)
        if not user_id:
            log.error("Could not resolve X user ID for @geniusmoneytax")
            return
        state["x_user_id"] = user_id
        log.info(f"Resolved @geniusmoneytax → user_id={user_id}")

    since_id = state.get("last_x_mention_id")
    mentions = get_x_mentions(user_id, creds, since_id)

    if not mentions:
        log.info("No new X mentions.")
        return

    log.info(f"Found {len(mentions)} new mention(s).")

    # Track newest mention ID for next run
    newest_id = max(int(m["id"]) for m in mentions)
    state["last_x_mention_id"] = str(newest_id)

    replied_ids  = set(state.get("replied_tweet_ids", []))
    liked_ids    = set(state.get("liked_tweet_ids", []))

    for mention in mentions:
        tweet_id = mention["id"]
        text     = mention.get("text", "")
        author   = mention.get("author_id", "unknown")
        created  = mention.get("created_at", "")

        log.info(f"  Tweet {tweet_id} | author={author} | text={text!r}")

        # Classify
        category = classify_text(text)
        log.info(f"  → classified as: {category}")

        entry = {
            "platform":   "x",
            "tweet_id":   tweet_id,
            "author_id":  author,
            "text":       text,
            "created_at": created,
            "category":   category,
            "action":     None,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }

        if category == "negative":
            log.warning(f"  ⚑ Flagging negative tweet {tweet_id} for review.")
            entry["action"] = "flagged"
            append_flagged({**entry, "reason": "negative sentiment"})
            append_log(entry)
            continue

        # Complex / unrecognised → flag
        if category not in TEMPLATES and category != "positive":
            log.info(f"  ⚑ Flagging unclassified tweet {tweet_id}.")
            entry["action"] = "flagged"
            append_flagged({**entry, "reason": "unclassified — needs review"})
            append_log(entry)
            continue

        # Positive → like (once)
        if category == "positive":
            if tweet_id not in liked_ids:
                log.info(f"  ♥ Liking tweet {tweet_id}")
                if not dry_run:
                    like_tweet(tweet_id, user_id, creds, dry_run)
                liked_ids.add(tweet_id)
                entry["action"] = "liked"
            else:
                log.info(f"  Already liked {tweet_id}, skipping.")
                entry["action"] = "skip_already_liked"
            append_log(entry)
            continue

        # Question / info request → reply
        reply_text = get_reply_text(category)
        if tweet_id in replied_ids:
            log.info(f"  Already replied to {tweet_id}, skipping.")
            entry["action"] = "skip_already_replied"
            append_log(entry)
            continue

        replies_this_hour = x_replies_this_hour(state)
        if replies_this_hour >= 5:
            log.warning(f"  Rate limit: {replies_this_hour} replies this hour. Flagging {tweet_id}.")
            entry["action"] = "flagged_rate_limit"
            append_flagged({**entry, "reason": "rate limit — reply deferred"})
            append_log(entry)
            continue

        log.info(f"  ↩ Replying to {tweet_id}: {reply_text!r}")
        if not dry_run:
            reply_to_tweet(tweet_id, reply_text, creds, dry_run)
            record_x_reply(state)
        else:
            log.info(f"  [DRY-RUN] Would reply: {reply_text}")

        replied_ids.add(tweet_id)
        entry["action"] = "replied"
        entry["reply_text"] = reply_text
        append_log(entry)

    state["replied_tweet_ids"] = list(replied_ids)
    state["liked_tweet_ids"]   = list(liked_ids)


def monitor_linkedin(state: dict, dry_run: bool):
    log.info("── Checking LinkedIn comments ──")
    try:
        creds = get_linkedin_credentials()
    except FileNotFoundError as e:
        log.error(str(e))
        return

    seen_ids = set(state.get("seen_linkedin_comment_ids", []))
    all_comments = load_json(DATA_DIR / "linkedin-comments.json", [])
    new_comments = []

    for share_urn in LINKEDIN_SHARE_URNS:
        log.info(f"  Checking {share_urn}")
        comments = get_linkedin_comments(share_urn, creds)
        log.info(f"  → {len(comments)} comment(s) found")

        for comment in comments:
            comment_id = comment.get("id") or comment.get("$id") or str(comment)
            if comment_id in seen_ids:
                continue

            author_urn = (
                comment.get("actor") or
                comment.get("commenter") or
                "unknown"
            )
            message_text = ""
            message_obj = comment.get("message", {})
            if isinstance(message_obj, dict):
                message_text = message_obj.get("text", "")
            elif isinstance(message_obj, str):
                message_text = message_obj

            created = comment.get("created", {})
            created_time = created.get("time", 0) if isinstance(created, dict) else 0

            category = classify_text(message_text)

            entry = {
                "platform":   "linkedin",
                "share_urn":  share_urn,
                "comment_id": comment_id,
                "author_urn": author_urn,
                "text":       message_text,
                "created_ms": created_time,
                "category":   category,
                "flagged":    category in ("negative", "interest") or category not in TEMPLATES,
                "timestamp":  datetime.now(timezone.utc).isoformat(),
            }

            if dry_run:
                log.info(f"  [DRY-RUN] Comment {comment_id} | category={category} | text={message_text!r}")

            if category == "negative" or category not in TEMPLATES:
                log.warning(f"  ⚑ LinkedIn comment {comment_id} flagged for review.")
                append_flagged({**entry, "reason": f"linkedin: {category}"})

            seen_ids.add(comment_id)
            new_comments.append(entry)
            append_log(entry)

    if new_comments:
        all_comments.extend(new_comments)
        save_json(DATA_DIR / "linkedin-comments.json", all_comments)
        log.info(f"  Saved {len(new_comments)} new LinkedIn comment(s).")
    else:
        log.info("  No new LinkedIn comments.")

    state["seen_linkedin_comment_ids"] = list(seen_ids)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def run_once(dry_run: bool):
    log.info(f"{'[DRY-RUN] ' if dry_run else ''}Starting monitor run — {datetime.now(timezone.utc).isoformat()}")
    state = load_state()

    monitor_x(state, dry_run)
    monitor_linkedin(state, dry_run)

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    log.info("Run complete. State saved.")


def main():
    parser = argparse.ArgumentParser(description="Genius Tax — Social Media Monitor")
    parser.add_argument("--once",     action="store_true",      help="Run once and exit")
    parser.add_argument("--interval", type=int, default=900,    help="Loop interval in seconds (default: 900)")
    parser.add_argument("--dry-run",  action="store_true",      help="Preview actions without posting")
    args = parser.parse_args()

    if args.once:
        run_once(args.dry_run)
    else:
        log.info(f"Starting continuous loop (interval={args.interval}s). Ctrl-C to stop.")
        while True:
            try:
                run_once(args.dry_run)
            except KeyboardInterrupt:
                log.info("Interrupted — exiting.")
                sys.exit(0)
            except Exception as e:
                log.error(f"Unhandled error in run: {e}", exc_info=True)
            log.info(f"Sleeping {args.interval}s until next run…")
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
