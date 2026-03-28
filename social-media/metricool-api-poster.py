#!/usr/bin/env python3
"""
metricool-api-poster.py
Pure REST API poster for Metricool — posts to Twitter, Facebook, Instagram, LinkedIn, TikTok.

Usage:
  python3 metricool-api-poster.py --text "post text" --schedule "2026-03-26 17:00"
  python3 metricool-api-poster.py --text "post text" --image /path/to/image.png --schedule "2026-03-26 17:00"
  python3 metricool-api-poster.py --text "post text" --schedule "2026-03-26 17:00" --channels twitter,instagram,linkedin,tiktok
  python3 metricool-api-poster.py --text "..." --schedule "..." --dry-run

API endpoint: POST /v2/scheduler/posts
Auth: X-Mc-Auth header + blogId/userId query params
"""

import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = DATA_DIR / "metricool-api-log.json"
SECRETS_FILE = Path.home() / ".openclaw" / "secrets" / "metricool.env"
IMAGE_URL_CACHE = DATA_DIR / "image-url-cache.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Metricool API ──────────────────────────────────────────────────────────────
BASE_URL = "https://app.metricool.com/api"

# Channel → provider network name + account ID mapping
# Accounts connected to blogId 6029996 (Genius Money / Genius Tax)
# All confirmed working via API test 2026-03-26
CHANNEL_PROVIDERS = {
    "facebook": {
        "network": "facebook",
        "id": "263328853786774",           # Facebook page ID
    },
    "instagram": {
        "network": "instagram",
        "id": "17841403854498977",          # Instagram business account ID (fbBusinessId)
    },
    "twitter": {
        "network": "twitter",
        "id": "geniusmoneyltd",             # Twitter handle (confirmed working)
    },
    "linkedin": {
        "network": "linkedin",
        "id": "urn:li:organization:2629878", # LinkedIn Company URN (confirmed working)
    },
    "tiktok": {
        "network": "tiktok",
        "id": "genius.money10",             # TikTok handle (confirmed working)
    },
    # YouTube intentionally excluded (video-only platform)
}

DEFAULT_CHANNELS = ["twitter", "facebook", "instagram", "linkedin", "tiktok"]

# Imgur anonymous client ID for image hosting (free, no auth needed)
IMGUR_CLIENT_ID = "546c25a59c58ad7"


# ─── Credentials ───────────────────────────────────────────────────────────────

def load_credentials() -> dict:
    """Load Metricool credentials from ~/.openclaw/secrets/metricool.env"""
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


# ─── Image Upload ───────────────────────────────────────────────────────────────

def load_image_cache() -> dict:
    """Load the local image URL cache."""
    if IMAGE_URL_CACHE.exists():
        try:
            return json.loads(IMAGE_URL_CACHE.read_text())
        except Exception:
            pass
    return {}


def save_image_cache(cache: dict):
    """Save the image URL cache."""
    IMAGE_URL_CACHE.write_text(json.dumps(cache, indent=2))


def upload_image_imgur(image_path: Path) -> str | None:
    """
    Upload an image to Imgur anonymously.
    Returns the public image URL, or None on failure.
    Caches results to avoid re-uploading the same image.
    """
    cache = load_image_cache()
    cache_key = f"{image_path.name}:{image_path.stat().st_size}"

    if cache_key in cache:
        print(f"  📋 Using cached image URL for {image_path.name}")
        return cache[cache_key]

    print(f"  📤 Uploading image to Imgur ({image_path.stat().st_size} bytes)...")

    try:
        image_data = image_path.read_bytes()
        b64_data = base64.b64encode(image_data).decode()

        resp = requests.post(
            "https://api.imgur.com/3/image",
            headers={"Authorization": f"Client-ID {IMGUR_CLIENT_ID}"},
            data={"image": b64_data, "type": "base64"},
            timeout=30,
        )

        if resp.status_code == 200:
            url = resp.json().get("data", {}).get("link")
            if url:
                print(f"  ✅ Imgur upload successful: {url}")
                cache[cache_key] = url
                save_image_cache(cache)
                return url
            else:
                print(f"  ❌ Imgur upload: no link in response")
        else:
            print(f"  ❌ Imgur upload failed: {resp.status_code} {resp.text[:200]}")

    except Exception as e:
        print(f"  ❌ Imgur upload error: {e}")

    return None


def upload_image_metricool_s3(image_path: Path, creds: dict) -> str | None:
    """
    Upload an image to Metricool via S3 presigned URL (requires premium plan feature).
    Returns the final file URL, or None on failure.
    """
    import hashlib

    token = creds["METRICOOL_USER_TOKEN"]
    user_id = creds["METRICOOL_USER_ID"]
    blog_id = creds["METRICOOL_BLOG_ID"]

    headers = {"X-Mc-Auth": token, "Content-Type": "application/json"}
    params = {"blogId": blog_id, "userId": user_id}

    image_data = image_path.read_bytes()
    file_size = len(image_data)
    suffix = image_path.suffix.lower().lstrip(".")
    content_type_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "webp": "image/webp"
    }
    content_type = content_type_map.get(suffix, "image/png")

    sha256 = hashlib.sha256(image_data).digest()
    hash_b64 = base64.b64encode(sha256).decode()

    transaction_body = {
        "resourceType": "planner",
        "contentType": content_type,
        "fileExtension": suffix,
        "parts": [{"size": file_size, "startByte": 0, "endByte": file_size, "hash": hash_b64}],
    }

    resp = requests.put(
        f"{BASE_URL}/v2/media/s3/upload-transactions",
        headers=headers, params=params, json=transaction_body,
    )

    if resp.status_code != 200:
        print(f"  ⚠️  Metricool S3 upload unavailable ({resp.status_code}): feature may require premium plan")
        return None

    tx = resp.json()
    presigned_url = tx.get("presignedUrl")
    file_url = tx.get("fileUrl")
    key = tx.get("key")
    bucket = tx.get("bucket")

    if not presigned_url:
        return None

    s3_resp = requests.put(presigned_url, data=image_data, headers={"Content-Type": content_type})
    if s3_resp.status_code not in (200, 204):
        return None

    patch_params = dict(params)
    if key:
        patch_params["key"] = key
    if bucket:
        patch_params["bucket"] = bucket

    requests.patch(
        f"{BASE_URL}/v2/media/s3/upload-transactions",
        headers=headers, params=patch_params,
        json={"simple": {"fileUrl": file_url}},
    )

    return file_url


def get_image_url(image_path: Path, creds: dict) -> str | None:
    """
    Get a public URL for the given image.
    Tries Metricool S3 first (premium), falls back to Imgur.
    """
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        return None

    # Try Metricool S3 (may not be available on current plan)
    url = upload_image_metricool_s3(image_path, creds)
    if url:
        return url

    # Fall back to Imgur
    return upload_image_imgur(image_path)


# ─── Post Scheduling ────────────────────────────────────────────────────────────

def schedule_post(
    text: str,
    schedule_dt: str,
    channels: list[str],
    image_path: Path | None,
    creds: dict,
    dry_run: bool = False,
) -> dict:
    """
    Schedule a post via Metricool REST API.
    Endpoint: POST /v2/scheduler/posts
    Returns the result dict.
    """
    token = creds["METRICOOL_USER_TOKEN"]
    user_id = creds["METRICOOL_USER_ID"]
    blog_id = creds["METRICOOL_BLOG_ID"]

    # Parse schedule time → ISO 8601 local time
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            naive_dt = datetime.strptime(schedule_dt, fmt)
            break
        except ValueError:
            continue
    else:
        print(f"ERROR: Invalid schedule format: {schedule_dt}. Use 'YYYY-MM-DD HH:MM'")
        sys.exit(1)

    dt_iso = naive_dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Build providers list (no status field — server assigns it)
    providers = []
    for channel in channels:
        channel_lower = channel.lower().strip()
        if channel_lower not in CHANNEL_PROVIDERS:
            print(f"WARNING: Unknown channel '{channel_lower}', skipping")
            continue
        providers.append(CHANNEL_PROVIDERS[channel_lower].copy())

    if not providers:
        print("ERROR: No valid channels specified")
        sys.exit(1)

    # Get image URL if provided
    media_urls = []
    if image_path:
        if dry_run:
            print(f"  [DRY RUN] Would upload: {image_path.name}")
        else:
            url = get_image_url(image_path, creds)
            if url:
                media_urls.append(url)
            else:
                print("WARNING: Image upload failed — posting without image")

    # Build post body
    post_body = {
        "text": text,
        "publicationDate": {
            "dateTime": dt_iso,
            "timezone": "Europe/London",
        },
        "providers": providers,
        "autoPublish": True,
    }

    if media_urls:
        post_body["media"] = media_urls

    headers = {
        "X-Mc-Auth": token,
        "Content-Type": "application/json",
    }
    params = {"blogId": blog_id, "userId": user_id}

    if dry_run:
        print(f"\n[DRY RUN] Would POST to {BASE_URL}/v2/scheduler/posts")
        print(f"  Params: {params}")
        print(f"  Body: {json.dumps(post_body, indent=2)}")
        return {"status": "dry_run", "body": post_body}

    print(f"\n📅 Scheduling post for {schedule_dt} UK on {', '.join(channels)}...")
    resp = requests.post(
        f"{BASE_URL}/v2/scheduler/posts",
        headers=headers,
        params=params,
        json=post_body,
        timeout=30,
    )

    result = {
        "status_code": resp.status_code,
        "response": None,
    }

    try:
        result["response"] = resp.json()
    except Exception:
        result["response"] = resp.text

    if resp.status_code in (200, 201):
        print(f"✅ Post scheduled successfully! Status: {resp.status_code}")
        resp_data = result["response"]
        data = resp_data.get("data", {}) if isinstance(resp_data, dict) else {}
        post_id = data.get("id")
        if post_id:
            print(f"   Post ID: {post_id}")
            result["post_id"] = post_id
    else:
        print(f"❌ Scheduling failed: {resp.status_code}")
        print(f"   Response: {str(result['response'])[:500]}")

    return result


# ─── Logging ───────────────────────────────────────────────────────────────────

def log_post(entry: dict):
    """Append a post entry to the JSON log file."""
    log = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text())
        except Exception:
            log = []
    log.append(entry)
    LOG_FILE.write_text(json.dumps(log, indent=2))


# ─── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Schedule posts to Twitter, Facebook, Instagram, LinkedIn, TikTok via Metricool REST API"
    )
    parser.add_argument("--text", required=True, help="Post text content")
    parser.add_argument("--image", help="Path to image file (optional)")
    parser.add_argument(
        "--schedule",
        required=True,
        help='Schedule time in UK (Europe/London) timezone. Format: "YYYY-MM-DD HH:MM"',
    )
    parser.add_argument(
        "--channels",
        default=",".join(DEFAULT_CHANNELS),
        help=f"Comma-separated channels (default: {','.join(DEFAULT_CHANNELS)}). Options: twitter,facebook,instagram,linkedin,tiktok",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")

    args = parser.parse_args()

    channels = [c.strip().lower() for c in args.channels.split(",") if c.strip()]
    image_path = Path(args.image).expanduser() if args.image else None

    creds = load_credentials()

    print(f"📣 Metricool API Poster")
    print(f"   Schedule : {args.schedule} UK")
    print(f"   Channels : {', '.join(channels)}")
    print(f"   Image    : {image_path.name if image_path else 'none'}")
    print(f"   Text     : {args.text[:80]}{'...' if len(args.text) > 80 else ''}")
    if args.dry_run:
        print(f"   Mode     : DRY RUN")
    print()

    result = schedule_post(
        text=args.text,
        schedule_dt=args.schedule,
        channels=channels,
        image_path=image_path,
        creds=creds,
        dry_run=args.dry_run,
    )

    # Log the attempt
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "schedule": args.schedule,
        "channels": channels,
        "text_preview": args.text[:100],
        "image": str(image_path) if image_path else None,
        "dry_run": args.dry_run,
        "result": {
            "status_code": result.get("status_code"),
            "post_id": result.get("post_id"),
            "success": result.get("status_code") in (200, 201),
        },
    }
    if not args.dry_run:
        log_post(log_entry)
        print(f"\n📝 Logged to {LOG_FILE}")


if __name__ == "__main__":
    main()
