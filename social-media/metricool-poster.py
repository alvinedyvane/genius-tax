#!/usr/bin/env python3
"""
metricool-poster.py
Playwright-based automation for scheduling posts on Metricool.

Usage:
  python3 metricool-poster.py --login
  python3 metricool-poster.py --post "text" --image /path/img.png --channels instagram,facebook --schedule "2026-03-26 09:00" --tz "Europe/London"
  python3 metricool-poster.py --post "text" --channels instagram,facebook --now
  python3 metricool-poster.py --queue-today [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ERROR_DIR = DATA_DIR / "metricool-errors"
STATE_FILE = DATA_DIR / "metricool-state.json"
LOG_FILE = DATA_DIR / "metricool-post-log.json"
CALENDAR_FILE = BASE_DIR / "content-calendar.md"
IMAGES_DIR = BASE_DIR / "images" / "branded"
SECRETS_FILE = Path.home() / ".openclaw" / "secrets" / "metricool.env"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ERROR_DIR.mkdir(parents=True, exist_ok=True)

METRICOOL_URL = "https://app.metricool.com"

# Branded image rotation list (in preference order for queue-today)
BRANDED_IMAGES = [
    "01-your-tax-sorted.png",
    "02-built-for-people.png",
    "03-three-steps.png",
    "04-simple-pricing.png",
    "06-pick-your-plan.png",
    "07-ready-sorted.png",
]

# UK posting schedule for queue-today
UK_SCHEDULE_TIMES = ["09:00", "13:00", "17:00"]


# ─── Credentials ──────────────────────────────────────────────────────────────
def load_credentials() -> tuple[str, str]:
    env = {}
    if SECRETS_FILE.exists():
        for line in SECRETS_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    email = env.get("METRICOOL_EMAIL") or os.environ.get("METRICOOL_EMAIL", "")
    password = env.get("METRICOOL_PASSWORD") or os.environ.get("METRICOOL_PASSWORD", "")
    if not email or not password:
        print("ERROR: METRICOOL_EMAIL / METRICOOL_PASSWORD not found in secrets file.")
        sys.exit(1)
    return email, password


# ─── Logging ──────────────────────────────────────────────────────────────────
def load_log() -> list[dict]:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def save_log(entries: list[dict]):
    LOG_FILE.write_text(json.dumps(entries, indent=2))


def already_posted(text: str, channel: str, log: list[dict]) -> bool:
    for entry in log:
        if entry.get("text") == text and channel in entry.get("channels", []):
            return True
    return False


def log_post(text: str, channels: list[str], schedule: str | None,
             image: str | None, result: str, dry_run: bool = False):
    log = load_log()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "text": text,
        "channels": channels,
        "schedule": schedule,
        "image": image,
        "result": result,
        "dry_run": dry_run,
    }
    log.append(entry)
    save_log(log)
    print(f"[LOG] {result} | channels={channels} | schedule={schedule}")


# ─── Browser helpers ──────────────────────────────────────────────────────────
def screenshot_error(page, name: str):
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = ERROR_DIR / f"{ts}-{name}.png"
    try:
        page.screenshot(path=str(path))
        print(f"[DEBUG] Screenshot saved: {path}")
    except Exception as e:
        print(f"[DEBUG] Could not take screenshot: {e}")


def wait_and_click(page, selector: str, timeout: int = 30_000, retries: int = 1):
    """Click with retry on failure."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            page.wait_for_selector(selector, timeout=timeout)
            page.click(selector, timeout=timeout)
            return
        except PlaywrightTimeout as e:
            last_err = e
            if attempt < retries:
                print(f"[RETRY] Retrying click on {selector!r}…")
                time.sleep(2)
    raise last_err


def wait_and_fill(page, selector: str, value: str, timeout: int = 30_000, retries: int = 1):
    last_err = None
    for attempt in range(retries + 1):
        try:
            page.wait_for_selector(selector, timeout=timeout)
            page.fill(selector, value, timeout=timeout)
            return
        except PlaywrightTimeout as e:
            last_err = e
            if attempt < retries:
                print(f"[RETRY] Retrying fill on {selector!r}…")
                time.sleep(2)
    raise last_err


# ─── Session management ───────────────────────────────────────────────────────
def save_state(context):
    state = context.storage_state()
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"[AUTH] Session saved → {STATE_FILE}")


def is_logged_in(page) -> bool:
    """Check if the current page looks like a logged-in dashboard.
    Note: Metricool SPA does NOT update the URL bar on login — URL stays at /login
    even when dashboard is visible. So check content, not URL.
    """
    try:
        # If we can see the main nav (Analytics, Planning, etc.) we're logged in
        content = page.inner_text("body")
        if "Analytics" in content and "Planning" in content and "Inbox" in content:
            return True
    except Exception:
        pass
    return False


def detect_auth_error(page) -> bool:
    """Detect if page shows an authentication error (e.g., session expired)."""
    try:
        page.wait_for_selector('text="You are not authenticated"', timeout=1000)
        return True
    except PlaywrightTimeout:
        pass

    # Check page content for auth error indicators.
    # NOTE: Do NOT use bare '"401" in content' — "401" appears legitimately
    # in page data (follower counts, image paths, etc.) causing false positives.
    content = page.content()
    if "not authenticated anymore" in content.lower():
        return True
    if "xhr - 401" in content.lower() or "xhr-401" in content.lower():
        return True
    if "click the button to log in again" in content.lower():
        return True

    return False


# ─── Login ────────────────────────────────────────────────────────────────────
def do_login(page, context, email: str, password: str, force_fresh: bool = False):
    print(f"[AUTH] Navigating to {METRICOOL_URL}/login …")
    page.goto(f"{METRICOOL_URL}/login", timeout=30_000)
    time.sleep(3)  # SPA needs time to fully render the login form

    # Check if already logged in via stored state
    # But also verify with a test request to avoid stale cookies
    if not force_fresh and is_logged_in(page):
        print("[AUTH] Checking if stored session is still valid…")
        # Metricool SPA: after navigation to /login with valid cookies,
        # dashboard content renders but URL stays at /login.
        # Check if dashboard content is already showing.
        time.sleep(4)
        if is_logged_in(page):
            print("[AUTH] Session is still valid.")
            return
        else:
            print("[AUTH] Stored session is stale, clearing and re-logging in.")
            context.clear_cookies()
            page.goto(f"{METRICOOL_URL}/login", timeout=15_000)
            time.sleep(3)

    # Even if force_fresh=True, check whether we're actually already logged in
    # (this handles false-positive re-auth triggers where the session is fine).
    if force_fresh and is_logged_in(page):
        print("[AUTH] force_fresh=True but session appears valid — skipping credential re-entry.")
        save_state(context)
        return

    print("[AUTH] Logging in …")

    # Handle "You are not authenticated anymore" intermediate 401 page.
    # Metricool sometimes shows this page (xhr-401) before the real login form.
    # It has a "Log in" button — click it to reach the actual login form.
    try:
        auth_error_btn = page.wait_for_selector(
            'button:has-text("Log in"), a:has-text("Log in"), [class*="login"]:has-text("Log in")',
            timeout=4_000,
        )
        page_content = page.inner_text("body")
        if "not authenticated" in page_content.lower() or "401" in page_content:
            print("[AUTH] Detected 401 intermediate page — clicking Log in button…")
            auth_error_btn.click()
            time.sleep(4)  # wait for actual login form to render
    except Exception:
        pass  # Not on the 401 page, proceed normally

    # Email field — try multiple selectors
    email_selectors = [
        'input[name="email"]',
        'input[type="email"]',
        'input[placeholder*="email" i]',
        'input[aria-label*="email" i]',
        '#email',
    ]
    for sel in email_selectors:
        try:
            page.wait_for_selector(sel, timeout=5_000)
            page.fill(sel, email)
            print(f"[AUTH] Filled email with selector: {sel}")
            break
        except PlaywrightTimeout:
            continue
    else:
        screenshot_error(page, "login-email-not-found")
        raise RuntimeError("Could not find email input on login page.")

    # Password field
    pwd_selectors = [
        'input[name="password"]',
        'input[type="password"]',
        'input[placeholder*="password" i]',
        'input[aria-label*="password" i]',
        '#password',
    ]
    for sel in pwd_selectors:
        try:
            page.wait_for_selector(sel, timeout=5_000)
            page.fill(sel, password)
            print(f"[AUTH] Filled password with selector: {sel}")
            break
        except PlaywrightTimeout:
            continue
    else:
        screenshot_error(page, "login-password-not-found")
        raise RuntimeError("Could not find password input on login page.")

    # Submit button — Metricool uses "Access" as the login button text
    submit_selectors = [
        'button:has-text("Access")',
        'button[type="submit"]',
        'button:has-text("Log in")',
        'button:has-text("Login")',
        'button:has-text("Sign in")',
        'input[type="submit"]',
        '[data-testid="login-submit"]',
        '[aria-label*="login" i]',
        '[aria-label*="sign in" i]',
    ]
    for sel in submit_selectors:
        try:
            page.wait_for_selector(sel, timeout=5_000)
            page.click(sel)
            print(f"[AUTH] Clicked submit with selector: {sel}")
            break
        except PlaywrightTimeout:
            continue
    else:
        screenshot_error(page, "login-submit-not-found")
        raise RuntimeError("Could not find login submit button.")

    # Wait for dashboard to load — Metricool SPA doesn't change URL after login
    # Just wait for the content to appear
    time.sleep(6)
    try:
        page.wait_for_selector('text="Analytics"', timeout=15_000)
    except PlaywrightTimeout:
        screenshot_error(page, "login-redirect-timeout")
        raise RuntimeError("Timed out waiting for dashboard after login.")

    if not is_logged_in(page):
        screenshot_error(page, "login-failed")
        raise RuntimeError(f"Login failed. Current URL: {page.url}")

    print(f"[AUTH] Logged in! URL: {page.url}")

    # Screenshot dashboard for verification
    dashboard_shot = DATA_DIR / "metricool-dashboard.png"
    page.screenshot(path=str(dashboard_shot))
    print(f"[AUTH] Dashboard screenshot saved → {dashboard_shot}")

    save_state(context)


# ─── Post creation ────────────────────────────────────────────────────────────
def navigate_to_planner(page):
    """Navigate to the planner/scheduler section."""
    print("[POST] Navigating to planner …")

    planner_selectors = [
        'a[href*="planner"]',
        'a[href*="scheduler"]',
        '[data-testid*="planner"]',
        '[aria-label*="planner" i]',
        'a:has-text("Planner")',
        'a:has-text("Planning")',
        'a:has-text("Scheduler")',
        'nav a:has-text("Plan")',
        '[data-testid="sidebar-planner"]',
    ]
    for sel in planner_selectors:
        try:
            page.wait_for_selector(sel, timeout=5_000)
            page.click(sel)
            page.wait_for_load_state("networkidle", timeout=15_000)
            
            # Check if we got an auth error instead
            if detect_auth_error(page):
                print("[POST] Auth error detected after clicking planner link, will retry with fresh login")
                raise RuntimeError("Session expired, need to re-login")
            
            print(f"[POST] Navigated to planner via {sel}")
            return
        except PlaywrightTimeout:
            continue
        except RuntimeError as e:
            if "Session expired" in str(e):
                raise

    # Fallback: try direct URL navigation
    planner_urls = [
        f"{METRICOOL_URL}/planner",
        f"{METRICOOL_URL}/scheduler",
        f"{METRICOOL_URL}/planning",
    ]
    for url in planner_urls:
        try:
            page.goto(url, timeout=15_000)
            page.wait_for_load_state("networkidle", timeout=15_000)
            
            if detect_auth_error(page):
                print("[POST] Auth error detected after planner navigation, will retry with fresh login")
                raise RuntimeError("Session expired, need to re-login")
            
            if "planner" in page.url or "scheduler" in page.url or "planning" in page.url:
                print(f"[POST] Navigated to planner via direct URL: {url}")
                return
        except RuntimeError as e:
            if "Session expired" in str(e):
                raise
        except Exception as e:
            print(f"[DEBUG] Failed to navigate to {url}: {e}")
            continue

    screenshot_error(page, "planner-not-found")
    raise RuntimeError("Could not navigate to planner/scheduler section.")


def click_create_post(page):
    """Click the create post button."""
    create_selectors = [
        'button:has-text("Create post")',
        'button:has-text("New post")',
        'button:has-text("Create")',
        '[data-testid*="create-post"]',
        '[data-testid*="new-post"]',
        '[aria-label*="create post" i]',
        '[aria-label*="new post" i]',
        'button.create-post',
        'button[class*="create"]',
        '.btn-create',
    ]
    for sel in create_selectors:
        try:
            page.wait_for_selector(sel, timeout=5_000)
            page.click(sel)
            page.wait_for_load_state("domcontentloaded", timeout=10_000)
            
            # Check if we got an auth error instead of the create post composer
            if detect_auth_error(page):
                print("[POST] Auth error detected after clicking create post, will retry with fresh login")
                raise RuntimeError("Session expired, need to re-login")
            
            print(f"[POST] Clicked create post via {sel}")
            return
        except PlaywrightTimeout:
            continue
        except RuntimeError as e:
            if "Session expired" in str(e):
                raise

    screenshot_error(page, "create-post-not-found")
    raise RuntimeError("Could not find 'Create post' button.")


def select_channels(page, channels: list[str]):
    """Select Instagram / Facebook channels in the post composer.
    
    The network selector uses font-awesome icons inside divs with cursor-pointer class.
    Each network is inside a div that can be clicked by finding the icon and traversing to the parent.
    """
    for channel in channels:
        ch = channel.strip().lower()
        try:
            # The network icons are: i[aria-label="instagram"], i[aria-label="facebook"], etc.
            icon_selector = f'i[aria-label="{ch}"]'
            page.wait_for_selector(icon_selector, timeout=5_000)
            
            # Click the icon's parent div (which has cursor-pointer class and is clickable)
            result = page.evaluate(f"""
                () => {{
                    const icon = document.querySelector('{icon_selector}');
                    if (!icon) return 'icon not found';
                    const div = icon.closest('div.cursor-pointer');
                    if (!div) return 'parent div not found';
                    div.click();
                    // Wait a moment for state change
                    return 'clicked';
                }}
            """)
            
            if result == 'clicked':
                print(f"[POST] Selected channel: {channel}")
            else:
                print(f"[WARN] Failed to select {channel}: {result}")
        except PlaywrightTimeout:
            print(f"[WARN] Could not find icon for channel: {channel}")


def enter_post_text(page, text: str):
    """Enter the post caption/text."""
    text_selectors = [
        'textarea[placeholder*="caption" i]',
        'textarea[placeholder*="text" i]',
        'textarea[placeholder*="post" i]',
        'textarea[aria-label*="caption" i]',
        'textarea[aria-label*="text" i]',
        '[contenteditable="true"]',
        '[data-testid*="caption"]',
        '[data-testid*="text"]',
        'textarea',
    ]
    for sel in text_selectors:
        try:
            page.wait_for_selector(sel, timeout=8_000)
            page.click(sel)
            page.fill(sel, text) if sel != '[contenteditable="true"]' else page.keyboard.type(text)
            print(f"[POST] Entered post text ({len(text)} chars) via {sel}")
            return
        except PlaywrightTimeout:
            continue

    screenshot_error(page, "text-input-not-found")
    raise RuntimeError("Could not find text input field in post composer.")


def upload_image(page, image_path: str):
    """Upload image to Metricool post (simplified/fast approach)."""
    if not Path(image_path).exists():
        print(f"[WARN] Image not found: {image_path} — skipping upload.")
        return

    print(f"[POST] Starting image upload: {image_path}")

    # Strategy 1: Direct hidden file input (fastest)
    file_inputs = page.query_selector_all('input[type="file"]')
    for fi in file_inputs:
        try:
            fi.set_input_files(image_path)
            print(f"[POST] ✅ Uploaded via hidden file input")
            time.sleep(2)
            return
        except Exception as e:
            continue

    # Strategy 2: Try targeted toolbar button with file-chooser
    toolbar_selectors = [
        'button[aria-label*="image" i]',
        'button[aria-label*="media" i]',
        'button[title*="image" i]',
        '[data-testid*="image"]',
        '[class*="toolbar"] button:first-child',
    ]
    for sel in toolbar_selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                with page.expect_file_chooser(timeout=3_000) as fc_info:
                    el.click()
                fc_info.value.set_files(image_path)
                print(f"[POST] ✅ Image uploaded via file-chooser from {sel}")
                time.sleep(2)
                return
        except Exception:
            continue

    # Strategy 3: "Add image" menu item
    try:
        add_img = page.query_selector('[role="menuitem"]:has-text("Add image"), button:has-text("Add image")')
        if add_img and add_img.is_visible():
            with page.expect_file_chooser(timeout=8_000) as fc_info:
                add_img.click()
            fc_info.value.set_files(image_path)
            print(f"[POST] ✅ Image uploaded via 'Add image' menu")
            time.sleep(2)
            return
    except Exception:
        pass

    screenshot_error(page, "upload-failed")
    print(f"[WARN] Could not upload image — proceeding anyway")


def set_schedule_datetime(page, schedule_dt: datetime):
    """Set the scheduled date and time in the post composer.
    
    The UI has a datetime button that opens a FullCalendar picker.
    We'll look for and click a time slot in the calendar that matches our target date/time.
    """
    print(f"[POST] Setting schedule: {schedule_dt.isoformat()}")
    
    target_date = schedule_dt.strftime("%Y-%m-%d")  # 2026-03-27
    target_hour = schedule_dt.strftime("%H")  # "09"
    target_minute = schedule_dt.strftime("%M")  # "00"
    target_time_hm = f"{int(target_hour):02d}:{target_minute}"  # "9:00" or "09:00"
    
    # The datetime button shows current date/time. Look for it and click to open picker.
    datetime_btn = None
    for btn in page.query_selector_all("button"):
        if btn.is_visible():
            txt = (btn.inner_text() or "").strip()
            # The button typically shows something like "Mar 26, 2026 1:36 PM"
            if "2026" in txt and ("AM" in txt or "PM" in txt):
                datetime_btn = btn
                break
    
    if not datetime_btn:
        print("[WARN] Could not find datetime button to open picker")
        return
    
    datetime_btn.click()
    time.sleep(1.5)
    
    # Now the FullCalendar should be visible. It shows a week view with time slots.
    # Each time slot is a cell in a table with data-time="HH:MM:SS" and data-date="YYYY-MM-DD"
    # We need to find the cell that matches both the date and time, then click it.
    
    try:
        # Use JavaScript to find and click the correct time slot
        result = page.evaluate(f"""
            () => {{
                // Find the cell for the target date and time
                const targetDate = '{target_date}';
                const targetTime = '{target_hour}:00:00';  // Always on the hour
                
                // Look for a td with data-date matching our target
                // and within that column, find the time row
                const allCells = document.querySelectorAll('td[data-date]');
                
                for (const cell of allCells) {{
                    const cellDate = cell.getAttribute('data-date');
                    if (cellDate === targetDate) {{
                        // This is the right day column. Now find the time slot.
                        // Time slots have data-time attribute in the table
                        // They might be in the same row or we need to look for the row with matching time
                        
                        // Try finding within this column
                        const colIndex = cell.cellIndex;
                        const table = cell.closest('table');
                        if (table) {{
                            const rows = table.querySelectorAll('tr');
                            for (const row of rows) {{
                                const rowTimeCell = row.querySelector('[data-time]');
                                if (rowTimeCell && rowTimeCell.getAttribute('data-time') === targetTime) {{
                                    // Found the right time! Click the cell in this row at our column
                                    const targetCell = row.querySelector(`td:nth-child(${{colIndex + 1}})`);
                                    if (targetCell) {{
                                        targetCell.click();
                                        return 'clicked time slot at ' + targetTime;
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
                
                // Fallback: just look for any cell with matching date and click it at the hour mark
                const cells = document.querySelectorAll(`td[data-date="${{targetDate}}"]`);
                if (cells.length > 0) {{
                    // Click on a mid-morning time slot (around 9-10 AM)
                    cells[0].click();
                    return 'clicked date cell (time may not be precise)';
                }}
                
                return 'could not find date/time slot in calendar';
            }}
        """)
        
        print(f"[POST] Calendar result: {result}")
        time.sleep(0.5)
        
        # Now close the calendar picker
        # Try multiple methods to close it
        closed = False
        
        # Method 1: Look for a close button or "Done" button in the calendar
        for btn_text in ["Done", "Close", "OK", "Apply"]:
            for btn in page.query_selector_all("button"):
                if btn.is_visible() and btn_text.lower() in (btn.inner_text() or "").lower():
                    try:
                        btn.click()
                        print(f"[POST] Closed calendar via '{btn_text}' button")
                        closed = True
                        break
                    except:
                        pass
            if closed:
                break
        
        # Method 2: If no button found, try pressing Escape
        if not closed:
            try:
                page.press("Escape")
                print("[POST] Closed calendar via Escape key")
                closed = True
            except:
                pass
        
        # Method 3: Click outside the calendar (on the form background)
        if not closed:
            try:
                page.click("[role='dialog']", force=True)  # Click the dialog overlay itself
                time.sleep(0.5)
            except:
                pass
        
        time.sleep(1)
        
    except Exception as e:
        print(f"[WARN] Error with calendar: {e}")
        # Try to close it anyway
        for _ in range(3):
            try:
                page.press("Escape")
                time.sleep(0.3)
            except:
                pass


def submit_post(page, now: bool = False):
    """Click the final publish or schedule button.
    
    The Schedule button is a split button at the bottom-right:
    - Main button (dark): "Schedule" → schedules at the selected datetime
    - Dropdown chevron (yellow/green): reveals "Publish now" option
    
    For immediate posting (now=True), click the dropdown to get "Publish now".
    For scheduled posting (now=False), click the main "Schedule" button.
    """
    screenshot_error(page, "submit-before-click")  # Debug screenshot
    
    if now:
        print("[POST] Mode: Post now (immediate)")
        
        # For immediate posting, click the dropdown chevron next to Schedule
        # to access "Publish now" or "Send now" option
        dropdown_selectors = [
            'button:near(button:has-text("Schedule"))',  # Button near Schedule button
            '[class*="split"] > button:last-child',  # Rightmost button in split button group
            'button[aria-label*="more" i]:near(button:has-text("Schedule"))',
            'svg[class*="chevron"]:near(button:has-text("Schedule"))',
        ]
        
        dropdown_clicked = False
        for sel in dropdown_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    print(f"[POST] Clicked dropdown via: {sel}")
                    dropdown_clicked = True
                    time.sleep(0.5)
                    break
            except Exception:
                continue
        
        if not dropdown_clicked:
            print("[DEBUG] Could not find dropdown chevron, trying direct 'Publish now' button...")
        
        # Now look for "Publish now" or "Post now" or "Send now" in the menu
        publish_now_selectors = [
            'button:has-text("Publish now")',
            'button:has-text("Post now")',
            'button:has-text("Send now")',
            '[role="menuitem"]:has-text("Publish now")',
            '[role="menuitem"]:has-text("Post now")',
            'div:has-text("Publish now")',
        ]
        
        for sel in publish_now_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    print(f"[POST] Clicked 'Publish now' via: {sel}")
                    page.wait_for_load_state("networkidle", timeout=15_000)
                    print("[POST] Post submitted (now mode)")
                    return
            except Exception:
                continue
        
        # Fallback: if no "Publish now" option, the dropdown might reveal other options
        screenshot_error(page, "submit-publish-now-not-found")
        raise RuntimeError("Could not find 'Publish now' option in dropdown menu.")
    
    else:
        print("[POST] Mode: Schedule at selected datetime")
        
        # For scheduled posting, look for the main "Schedule" button
        # This is the dark filled button (not the dropdown chevron)
        schedule_selectors = [
            'button:has-text("Schedule")',
            'button[class*="schedule"]:visible',
            '[data-testid*="schedule-post"]',
            '[aria-label*="schedule" i]',
        ]
        
        schedule_clicked = False
        for sel in schedule_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    # Allow partial text match — the button may have a chevron sibling
                    # whose text_content bleeds in, or have trailing whitespace.
                    text = (el.text_content() or "").strip().lower()
                    if "schedule" in text:
                        el.click()
                        print(f"[POST] Clicked Schedule button via: {sel} (text: '{text}')")
                        schedule_clicked = True
                        break
            except Exception:
                continue

        # Broader fallback: find any visible button whose text starts with "Schedule"
        if not schedule_clicked:
            try:
                buttons = page.query_selector_all('button')
                for btn in buttons:
                    if btn.is_visible():
                        t = (btn.text_content() or "").strip().lower()
                        if t.startswith("schedule"):
                            btn.click()
                            print(f"[POST] Clicked Schedule button via fallback scan (text: '{t}')")
                            schedule_clicked = True
                            break
            except Exception:
                pass

        if not schedule_clicked:
            screenshot_error(page, "submit-schedule-not-found")
            raise RuntimeError("Could not find 'Schedule' button at bottom-right.")
        
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
            print("[POST] Post submitted (scheduled mode)")
        except PlaywrightTimeout:
            print("[WARN] Timeout waiting for page load after schedule button click, but continuing...")
        
        return


# ─── Core post flow ───────────────────────────────────────────────────────────
def create_post(
    page,
    context,
    text: str,
    channels: list[str],
    schedule: str | None = None,
    tz_name: str = "Europe/London",
    image: str | None = None,
    now: bool = False,
    dry_run: bool = False,
    email: str = "",
    password: str = "",
):
    log = load_log()

    # Duplicate check
    for ch in channels:
        if already_posted(text, ch, log):
            print(f"[SKIP] Already posted to {ch}: {text[:60]}…")
            return False

    if dry_run:
        print(f"[DRY-RUN] Would post to {channels}:")
        print(f"  Text: {text[:120]}…")
        print(f"  Image: {image}")
        print(f"  Schedule: {schedule} ({tz_name})")
        log_post(text, channels, schedule, image, "dry-run", dry_run=True)
        return True

    # Parse schedule
    schedule_dt = None
    if schedule and not now:
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            import datetime as dt_mod
            tz = dt_mod.timezone.utc
            print(f"[WARN] Unknown timezone {tz_name!r}, using UTC.")
        naive_dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
        schedule_dt = naive_dt.replace(tzinfo=tz)

    max_retries = 2
    for attempt in range(max_retries):
        try:
            navigate_to_planner(page)
            click_create_post(page)
            time.sleep(1)

            select_channels(page, channels)
            enter_post_text(page, text)

            if image:
                upload_image(page, image)

            if schedule_dt:
                set_schedule_datetime(page, schedule_dt)

            submit_post(page, now=now)
            save_state(context)

            schedule_label = schedule if schedule else ("now" if now else "draft")
            log_post(text, channels, schedule_label, image, "success")
            return True

        except RuntimeError as e:
            if "Session expired" in str(e) and attempt < max_retries - 1:
                print(f"[AUTH] Session expired, re-authenticating (attempt {attempt + 1}/{max_retries})...")
                if email and password:
                    try:
                        do_login(page, context, email, password, force_fresh=True)
                        print(f"[AUTH] Re-authentication successful, retrying post...")
                        time.sleep(2)
                        continue
                    except Exception as reauth_err:
                        print(f"[ERROR] Re-authentication failed: {reauth_err}")
                        log_post(text, channels, schedule, image, f"error: re-auth failed: {reauth_err}")
                        return False
                else:
                    print(f"[ERROR] No credentials available to re-authenticate")
                    log_post(text, channels, schedule, image, f"error: session expired, no credentials to re-auth")
                    return False
            else:
                screenshot_error(page, "post-error")
                print(f"[ERROR] Post failed: {e}")
                traceback.print_exc()
                log_post(text, channels, schedule, image, f"error: {e}")
                return False
        except Exception as e:
            screenshot_error(page, "post-error")
            print(f"[ERROR] Post failed: {e}")
            traceback.print_exc()
            log_post(text, channels, schedule, image, f"error: {e}")
            return False
    
    return False


# ─── Queue-today ──────────────────────────────────────────────────────────────
def parse_today_content() -> list[dict]:
    """
    Parse content-calendar.md for today's Instagram posts.
    Returns list of {text, slot} dicts (slot: morning/afternoon/evening).
    """
    if not CALENDAR_FILE.exists():
        print(f"[ERROR] Calendar not found: {CALENDAR_FILE}")
        return []

    content = CALENDAR_FILE.read_text()
    today = datetime.now().strftime("%B %-d, %Y").upper()  # e.g. MARCH 25, 2026
    today_alt = datetime.now().strftime("%B %d, %Y").upper()  # with leading zero

    # Find today's section
    pattern = rf"(##\s+{re.escape(today)}.*?)(?=\n## [A-Z]|\Z)"
    alt_pattern = rf"(##\s+{re.escape(today_alt)}.*?)(?=\n## [A-Z]|\Z)"

    section = None
    for pat in [pattern, alt_pattern]:
        m = re.search(pat, content, re.DOTALL | re.IGNORECASE)
        if m:
            section = m.group(1)
            break

    if not section:
        print(f"[WARN] No content found for today ({today}) in calendar.")
        return []

    # Find the Instagram subsection
    insta_match = re.search(r"###\s+Instagram(.*?)(?=\n###|\n##|\Z)", section, re.DOTALL | re.IGNORECASE)
    if not insta_match:
        print("[WARN] No Instagram section found for today.")
        return []

    insta_section = insta_match.group(1)

    # Extract Post 1, Post 2, Post 3 or Morning/Afternoon/Evening
    posts = []
    # Try "**Post N:**" pattern first
    post_matches = re.finditer(r"\*\*Post \d+:\*\*\s*(.*?)(?=\*\*Post \d+:\*\*|\Z)", insta_section, re.DOTALL)
    slots = ["morning", "afternoon", "evening"]
    for i, m in enumerate(post_matches):
        text = m.group(1).strip()
        if text:
            posts.append({"text": text, "slot": slots[i] if i < len(slots) else f"post{i+1}"})

    # Fallback: try **Morning:**/**Afternoon:**/**Evening:** pattern
    if not posts:
        for slot in ["morning", "afternoon", "evening"]:
            m = re.search(rf"\*\*{slot}:\*\*\s*(.*?)(?=\*\*(?:morning|afternoon|evening):\*\*|\Z)",
                          insta_section, re.DOTALL | re.IGNORECASE)
            if m:
                text = m.group(1).strip()
                if text:
                    posts.append({"text": text, "slot": slot})

    print(f"[QUEUE] Found {len(posts)} Instagram post(s) for today.")
    return posts


def pick_image(slot: str, index: int) -> str | None:
    """Pick a branded image based on slot/index."""
    available = [IMAGES_DIR / img for img in BRANDED_IMAGES if (IMAGES_DIR / img).exists()]
    if not available:
        return None
    # Rotate through images based on index
    chosen = available[index % len(available)]
    return str(chosen)


def do_queue_today(page, context, dry_run: bool = False, email: str = "", password: str = ""):
    """Queue today's content from content-calendar.md."""
    posts = parse_today_content()
    if not posts:
        print("[QUEUE] Nothing to schedule today.")
        return

    today_date = datetime.now().strftime("%Y-%m-%d")
    times = UK_SCHEDULE_TIMES  # 09:00, 13:00, 17:00

    for i, post in enumerate(posts):
        slot = post["slot"]
        text = post["text"]
        schedule_time = times[i] if i < len(times) else times[-1]
        schedule = f"{today_date} {schedule_time}"
        image = pick_image(slot, i)

        print(f"\n[QUEUE] Scheduling {slot} post at {schedule} UK time …")
        success = create_post(
            page, context,
            text=text,
            channels=["instagram", "facebook"],
            schedule=schedule,
            tz_name="Europe/London",
            image=image,
            dry_run=dry_run,
            email=email,
            password=password,
        )
        if success:
            print(f"[QUEUE] ✓ {slot} post scheduled.")
        else:
            print(f"[QUEUE] ✗ {slot} post failed.")

        time.sleep(2)  # brief pause between posts


# ─── Browser context factory ──────────────────────────────────────────────────
def make_browser(playwright, headed: bool):
    browser = playwright.chromium.launch(headless=not headed)

    # Load saved session state if it exists
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            context = browser.new_context(storage_state=state)
            print("[AUTH] Loaded saved session state.")
        except Exception as e:
            print(f"[AUTH] Could not load saved state ({e}), starting fresh.")
            context = browser.new_context()
    else:
        context = browser.new_context()

    context.set_default_timeout(30_000)
    page = context.new_page()
    return browser, context, page


# ─── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Metricool post scheduler via Playwright")
    parser.add_argument("--login", action="store_true", help="Login and save session")
    parser.add_argument("--post", metavar="TEXT", help="Post text")
    parser.add_argument("--image", metavar="PATH", help="Path to image file")
    parser.add_argument("--channels", metavar="CHANNELS", default="instagram,facebook",
                        help="Comma-separated channels (instagram,facebook)")
    parser.add_argument("--schedule", metavar="DATETIME",
                        help='Schedule datetime: "YYYY-MM-DD HH:MM"')
    parser.add_argument("--tz", metavar="TIMEZONE", default="Europe/London",
                        help="Timezone for scheduled datetime (default: Europe/London)")
    parser.add_argument("--now", action="store_true", help="Post immediately")
    parser.add_argument("--queue-today", action="store_true",
                        help="Queue today's content from content-calendar.md")
    parser.add_argument("--headed", action="store_true",
                        help="Run with visible browser (for debugging)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without actually posting")

    args = parser.parse_args()

    if not any([args.login, args.post, args.queue_today]):
        parser.print_help()
        sys.exit(1)

    email, password = load_credentials()
    channels = [c.strip().lower() for c in args.channels.split(",") if c.strip()]

    with sync_playwright() as playwright:
        browser, context, page = make_browser(playwright, headed=args.headed)

        try:
            # Always ensure we're logged in
            do_login(page, context, email, password)

            if args.login:
                print("[AUTH] Login complete. Session saved.")

            elif args.queue_today:
                do_queue_today(page, context, dry_run=args.dry_run, email=email, password=password)

            elif args.post:
                create_post(
                    page, context,
                    text=args.post,
                    channels=channels,
                    schedule=args.schedule,
                    tz_name=args.tz,
                    image=args.image,
                    now=args.now,
                    dry_run=args.dry_run,
                    email=email,
                    password=password,
                )

        except KeyboardInterrupt:
            print("\n[INFO] Interrupted.")
        except Exception as e:
            screenshot_error(page, "fatal-error")
            print(f"[FATAL] {e}")
            traceback.print_exc()
            sys.exit(1)
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
