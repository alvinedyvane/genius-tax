#!/usr/bin/env python3
"""
metricool-monitor.py
Monitors engagement (comments, replies, DMs) across all channels via Metricool internal API.
Alerts Donna (OpenClaw) when new engagement is detected.

Usage: python3 metricool-monitor.py
"""

import json, os, sys, time, subprocess
from datetime import datetime, timezone
from pathlib import Path

SECRETS = Path.home() / ".openclaw/secrets/metricool.env"
STATE_FILE = Path(__file__).parent / "data/metricool-monitor-state.json"
LOG_FILE = Path(__file__).parent / "data/metricool-monitor-log.json"

BLOG_ID = "6029996"
USER_ID = "4656212"

def load_creds():
    env = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env.get("METRICOOL_EMAIL", ""), env.get("METRICOOL_PASSWORD", "")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_seen_posts": {}, "last_check": None, "reported_engagements": []}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_session_token():
    """Login to Metricool and get a session JWT token."""
    from playwright.sync_api import sync_playwright
    
    email, password = load_creds()
    token = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        responses = {}
        def on_response(response):
            if 'tokens?' in response.url:
                try:
                    responses[response.url] = response.json()
                except:
                    pass
        page.on("response", on_response)
        
        page.goto("https://app.metricool.com/login")
        time.sleep(3)
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', password)
        page.click('button:has-text("Access")')
        time.sleep(6)
        
        for url, body in responses.items():
            if 'data' in body and 'token' in body.get('data', {}):
                token = body['data']['token']
                break
        
        browser.close()
    
    return token

def check_engagement(jwt_token):
    """Pull recent posts and check for new comments/replies."""
    import urllib.request
    
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    networks = ["facebook", "instagram", "twitter", "linkedin"]
    new_engagement = []
    state = load_state()
    
    for network in networks:
        try:
            # Get recent posts
            from_date = "2026-03-01T00:00:00"
            to_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            
            url = f"https://app.metricool.com/api/v2/analytics/posts/{network}?from={from_date}&to={to_date}&timezone=America/Barbados&userId={USER_ID}&blogId={BLOG_ID}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            
            posts = data.get("data", [])
            for post in posts:
                post_id = post.get("postId", "")
                comments = post.get("comments", 0) or 0
                reactions = post.get("reactions", 0) or post.get("like", 0) or 0
                
                key = f"{network}:{post_id}"
                prev = state["last_seen_posts"].get(key, {"comments": 0, "reactions": 0})
                
                if comments > prev["comments"]:
                    delta = comments - prev["comments"]
                    new_engagement.append({
                        "network": network,
                        "post_id": post_id,
                        "type": "comment",
                        "count": delta,
                        "text": post.get("text", "")[:80]
                    })
                
                state["last_seen_posts"][key] = {"comments": comments, "reactions": reactions}
        
        except Exception as e:
            print(f"[{network}] Error: {e}")
    
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    
    return new_engagement

def alert_donna(engagements):
    """Send alert via OpenClaw."""
    lines = []
    for e in engagements:
        lines.append(f"- {e['network'].upper()}: +{e['count']} comment(s) on post: \"{e['text']}\"")
    
    msg = "🔔 SOCIAL ENGAGEMENT ALERT\n\n" + "\n".join(lines) + "\n\nCheck Metricool for details and respond."
    
    # Write to a temp file for OpenClaw to pick up, or print to stdout
    print(msg)
    return msg

if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%H:%M')}] Metricool monitor starting...")
    
    try:
        jwt = get_session_token()
        if not jwt:
            print("❌ Could not get JWT token")
            sys.exit(1)
        
        engagements = check_engagement(jwt)
        
        if engagements:
            msg = alert_donna(engagements)
            print(f"✅ {len(engagements)} new engagement(s) detected")
        else:
            print("✅ No new engagement")
    
    except Exception as e:
        print(f"❌ Monitor error: {e}")
        import traceback
        traceback.print_exc()
