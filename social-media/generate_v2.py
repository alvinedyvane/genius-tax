#!/usr/bin/env python3
"""Generate 4 premium Genius Tax social media images using Playwright."""

import base64
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

LOGOS_DIR = Path("/Users/donnapaulsen/Projects/genius-tax/logos")
OUTPUT_DIR = Path("/Users/donnapaulsen/Projects/genius-tax/social-media/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def b64(filename):
    with open(LOGOS_DIR / filename, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Pre-load logos
white_logo = b64("gws-white.png")
colour_logo = b64("gws-full-colour.png")
pink_icon = b64("gm-icon-pink.png")

# ─────────────────────────────────────────────
# IMAGE 1: Countdown Urgency (1080x1080)
# ─────────────────────────────────────────────
html_1 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1080px;
    height: 1080px;
    background: #1a1a1a;
    font-family: 'Montserrat', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 72px 80px 56px;
    overflow: hidden;
  }}

  .logo-wrap {{
    width: 100%;
    display: flex;
    justify-content: flex-start;
  }}

  .logo {{
    height: 52px;
    width: auto;
  }}

  .main-content {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    margin-top: -20px;
  }}

  .countdown-label-top {{
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.25em;
    color: rgba(255,255,255,0.45);
    text-transform: uppercase;
    margin-bottom: 12px;
  }}

  .countdown-number {{
    font-size: 240px;
    font-weight: 900;
    color: #E5007D;
    line-height: 0.85;
    letter-spacing: -8px;
    /* subtle glow */
    text-shadow: 0 0 120px rgba(229,0,125,0.35), 0 0 40px rgba(229,0,125,0.2);
  }}

  .countdown-days {{
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 0.22em;
    color: #ffffff;
    text-transform: uppercase;
    margin-top: 8px;
  }}

  .divider {{
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, #E5007D, rgba(229,0,125,0.3));
    border-radius: 2px;
    margin: 32px 0 28px;
  }}

  .tagline {{
    font-size: 28px;
    font-weight: 600;
    color: rgba(255,255,255,0.85);
    letter-spacing: 0.04em;
  }}

  .bottom-section {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    width: 100%;
  }}

  .pill-row {{
    display: flex;
    gap: 20px;
  }}

  .pill {{
    background: #E5007D;
    color: #ffffff;
    font-family: 'Montserrat', sans-serif;
    font-size: 20px;
    font-weight: 700;
    padding: 18px 44px;
    border-radius: 60px;
    letter-spacing: 0.03em;
    box-shadow: 0 8px 32px rgba(229,0,125,0.35);
  }}

  .pill.secondary {{
    background: transparent;
    border: 2px solid rgba(229,0,125,0.7);
    color: rgba(255,255,255,0.9);
    box-shadow: none;
  }}

  .footer-url {{
    font-size: 16px;
    font-weight: 500;
    color: rgba(255,255,255,0.3);
    letter-spacing: 0.08em;
    text-transform: lowercase;
  }}
</style>
</head>
<body>
  <div class="logo-wrap">
    <img class="logo" src="data:image/png;base64,{white_logo}" alt="Genius Money">
  </div>

  <div class="main-content">
    <div class="countdown-label-top">MTD Deadline</div>
    <div class="countdown-number">13</div>
    <div class="countdown-days">Days Until MTD</div>
    <div class="divider"></div>
    <div class="tagline">Are you ready?</div>
  </div>

  <div class="bottom-section">
    <div class="pill-row">
      <div class="pill">From £199/yr</div>
      <div class="pill secondary">From £299/yr</div>
    </div>
    <div class="footer-url">geniustax.co.uk</div>
  </div>
</body>
</html>"""

# ─────────────────────────────────────────────
# IMAGE 2: Early Bird Offer (1080x1080)
# ─────────────────────────────────────────────
html_2 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1080px;
    height: 1080px;
    background: #ffffff;
    font-family: 'Montserrat', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 56px;
    overflow: hidden;
    position: relative;
  }}

  .top-strip {{
    width: 100%;
    height: 8px;
    background: linear-gradient(90deg, #E5007D, #ff4da6);
    flex-shrink: 0;
  }}

  .content {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    flex: 1;
    justify-content: center;
    padding: 0 100px;
    margin-top: -30px;
  }}

  .badge {{
    background: rgba(229,0,125,0.08);
    border: 1.5px solid rgba(229,0,125,0.25);
    color: #E5007D;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.2em;
    padding: 8px 24px;
    border-radius: 40px;
    text-transform: uppercase;
    margin-bottom: 20px;
  }}

  .early-bird {{
    font-size: 72px;
    font-weight: 900;
    color: #E5007D;
    letter-spacing: -1px;
    line-height: 1;
    text-transform: uppercase;
  }}

  .plan-name {{
    font-size: 26px;
    font-weight: 600;
    color: #444;
    margin-top: 8px;
    margin-bottom: 28px;
    letter-spacing: 0.05em;
  }}

  .price-row {{
    display: flex;
    align-items: flex-end;
    gap: 6px;
    margin-bottom: 6px;
  }}

  .price-main {{
    font-size: 108px;
    font-weight: 900;
    color: #E5007D;
    line-height: 1;
    letter-spacing: -4px;
  }}

  .price-period {{
    font-size: 26px;
    font-weight: 600;
    color: #999;
    margin-bottom: 14px;
  }}

  .price-was {{
    font-size: 20px;
    font-weight: 500;
    color: #bbb;
    text-decoration: line-through;
    margin-bottom: 4px;
  }}

  .price-monthly {{
    font-size: 20px;
    font-weight: 600;
    color: #666;
    margin-bottom: 32px;
  }}

  .divider {{
    width: 48px;
    height: 3px;
    background: #E5007D;
    border-radius: 2px;
    margin-bottom: 28px;
  }}

  .features {{
    display: flex;
    flex-direction: column;
    gap: 14px;
    width: 100%;
    max-width: 480px;
    margin-bottom: 36px;
  }}

  .feature {{
    display: flex;
    align-items: center;
    gap: 14px;
    font-size: 19px;
    font-weight: 600;
    color: #2D2D2D;
  }}

  .check {{
    width: 28px;
    height: 28px;
    background: #E5007D;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 14px;
    font-weight: 700;
    flex-shrink: 0;
  }}

  .cta-btn {{
    background: #E5007D;
    color: #ffffff;
    font-family: 'Montserrat', sans-serif;
    font-size: 20px;
    font-weight: 700;
    padding: 20px 56px;
    border-radius: 60px;
    letter-spacing: 0.02em;
    box-shadow: 0 12px 40px rgba(229,0,125,0.3);
    margin-bottom: 0;
  }}

  .bottom-logo-wrap {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
  }}

  .bottom-logo {{
    height: 36px;
    width: auto;
    opacity: 0.6;
  }}
</style>
</head>
<body>
  <div class="top-strip"></div>

  <div class="content">
    <div class="badge">Limited Time</div>
    <div class="early-bird">Early Bird</div>
    <div class="plan-name">Growth Plan</div>

    <div class="price-row">
      <div class="price-main">£299</div>
      <div class="price-period">/year</div>
    </div>
    <div class="price-was">£588/yr</div>
    <div class="price-monthly">or £30/month</div>

    <div class="divider"></div>

    <div class="features">
      <div class="feature">
        <div class="check">✓</div>
        Sage software included
      </div>
      <div class="feature">
        <div class="check">✓</div>
        Quarterly HMRC submissions
      </div>
      <div class="feature">
        <div class="check">✓</div>
        Dedicated account manager
      </div>
    </div>

    <div class="cta-btn">Sign up before 5 April →</div>
  </div>

  <div class="bottom-logo-wrap">
    <img class="bottom-logo" src="data:image/png;base64,{colour_logo}" alt="Genius Money">
  </div>
</body>
</html>"""

# ─────────────────────────────────────────────
# IMAGE 3: LinkedIn Landscape (1200x630)
# ─────────────────────────────────────────────
html_3 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1200px;
    height: 630px;
    background: #1a1a1a;
    font-family: 'Montserrat', sans-serif;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  .main-row {{
    display: flex;
    flex: 1;
    overflow: hidden;
  }}

  /* LEFT PANEL — 60% */
  .left {{
    width: 60%;
    padding: 52px 52px 40px 60px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border-right: 1px solid rgba(255,255,255,0.06);
  }}

  .left-top {{}}

  .headline {{
    font-size: 52px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1.0;
    letter-spacing: -1px;
    margin-bottom: 10px;
  }}

  .sub-headline {{
    font-size: 18px;
    font-weight: 500;
    color: rgba(255,255,255,0.45);
    letter-spacing: 0.02em;
    margin-bottom: 22px;
  }}

  .pink-rule {{
    width: 56px;
    height: 3px;
    background: #E5007D;
    border-radius: 2px;
    margin-bottom: 24px;
  }}

  .cards-row {{
    display: flex;
    gap: 16px;
  }}

  .card {{
    flex: 1;
    background: #2D2D2D;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 20px 22px;
  }}

  .card-tier {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: rgba(255,255,255,0.35);
    text-transform: uppercase;
    margin-bottom: 4px;
  }}

  .card-price {{
    font-size: 32px;
    font-weight: 900;
    color: #E5007D;
    margin-bottom: 2px;
    letter-spacing: -0.5px;
  }}

  .card-period {{
    font-size: 12px;
    font-weight: 500;
    color: rgba(255,255,255,0.4);
    margin-bottom: 12px;
  }}

  .card-feature {{
    font-size: 12px;
    font-weight: 500;
    color: rgba(255,255,255,0.65);
    padding: 4px 0;
    border-top: 1px solid rgba(255,255,255,0.06);
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .card-feature::before {{
    content: '·';
    color: #E5007D;
    font-size: 18px;
    line-height: 1;
  }}

  /* RIGHT PANEL — 40% */
  .right {{
    width: 40%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 50px;
    position: relative;
  }}

  .countdown-big {{
    font-size: 200px;
    font-weight: 900;
    color: #E5007D;
    line-height: 0.85;
    letter-spacing: -8px;
    text-shadow: 0 0 100px rgba(229,0,125,0.3);
  }}

  .days-left {{
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: rgba(255,255,255,0.7);
    text-transform: uppercase;
    margin-top: 8px;
  }}

  .right-logo {{
    position: absolute;
    bottom: 40px;
    right: 50px;
    height: 28px;
    width: auto;
    opacity: 0.7;
  }}

  /* FOOTER */
  .footer {{
    height: 44px;
    background: rgba(229,0,125,0.12);
    border-top: 1px solid rgba(229,0,125,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}

  .footer-url {{
    font-size: 14px;
    font-weight: 600;
    color: rgba(255,255,255,0.5);
    letter-spacing: 0.12em;
    text-transform: lowercase;
  }}
</style>
</head>
<body>
  <div class="main-row">
    <!-- LEFT -->
    <div class="left">
      <div class="left-top">
        <div class="headline">Making Tax<br>Digital</div>
        <div class="sub-headline">is mandatory from April 2026</div>
        <div class="pink-rule"></div>
        <div class="cards-row">
          <div class="card">
            <div class="card-tier">Essential</div>
            <div class="card-price">£199</div>
            <div class="card-period">per year</div>
            <div class="card-feature">MTD-compliant filing</div>
            <div class="card-feature">Quarterly submissions</div>
            <div class="card-feature">HMRC registered</div>
          </div>
          <div class="card">
            <div class="card-tier">Growth</div>
            <div class="card-price">£299</div>
            <div class="card-period">per year</div>
            <div class="card-feature">Sage software included</div>
            <div class="card-feature">Dedicated account mgr</div>
            <div class="card-feature">Priority support</div>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="right">
      <div class="countdown-big">13</div>
      <div class="days-left">Days Left</div>
      <img class="right-logo" src="data:image/png;base64,{white_logo}" alt="Genius Money">
    </div>
  </div>

  <div class="footer">
    <div class="footer-url">geniustax.co.uk/signup</div>
  </div>
</body>
</html>"""

# ─────────────────────────────────────────────
# IMAGE 4: Story (1080x1920) - Who Needs MTD
# ─────────────────────────────────────────────
html_4 = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1080px;
    height: 1920px;
    background: linear-gradient(175deg, #1a1a1a 0%, #2D0F1C 45%, #E5007D 100%);
    font-family: 'Montserrat', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 80px 80px 72px;
    overflow: hidden;
    position: relative;
  }}

  /* subtle texture overlay */
  body::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(229,0,125,0.12) 0%, transparent 60%);
    pointer-events: none;
  }}

  .top-logo {{
    height: 56px;
    width: auto;
    margin-bottom: 80px;
    z-index: 1;
  }}

  .section {{
    z-index: 1;
    width: 100%;
  }}

  .who-label {{
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.22em;
    color: rgba(255,255,255,0.45);
    text-transform: uppercase;
    margin-bottom: 16px;
    text-align: center;
  }}

  .who-headline {{
    font-size: 76px;
    font-weight: 900;
    color: #ffffff;
    text-align: center;
    line-height: 1.0;
    letter-spacing: -2px;
    text-transform: uppercase;
    margin-bottom: 60px;
  }}

  .bullet-list {{
    display: flex;
    flex-direction: column;
    gap: 28px;
    width: 100%;
    margin-bottom: 72px;
  }}

  .bullet {{
    display: flex;
    align-items: center;
    gap: 24px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 24px 32px;
    backdrop-filter: blur(10px);
  }}

  .bullet-icon {{
    width: 44px;
    height: 44px;
    background: #E5007D;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 20px;
    font-weight: 700;
    flex-shrink: 0;
  }}

  .bullet-text {{
    font-size: 24px;
    font-weight: 600;
    color: #ffffff;
    letter-spacing: 0.01em;
  }}

  .pink-divider {{
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
    margin-bottom: 72px;
  }}

  .get-sorted-label {{
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.22em;
    color: rgba(255,255,255,0.6);
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 12px;
  }}

  .big-price {{
    font-size: 120px;
    font-weight: 900;
    color: #ffffff;
    text-align: center;
    line-height: 1;
    letter-spacing: -4px;
    margin-bottom: 48px;
    text-shadow: 0 4px 40px rgba(0,0,0,0.3);
  }}

  .signup-btn {{
    background: rgba(255,255,255,0.95);
    color: #E5007D;
    font-family: 'Montserrat', sans-serif;
    font-size: 22px;
    font-weight: 700;
    padding: 24px 72px;
    border-radius: 60px;
    letter-spacing: 0.03em;
    margin-bottom: 0;
    box-shadow: 0 12px 48px rgba(0,0,0,0.25);
    text-align: center;
  }}

  .spacer {{ flex: 1; }}

  .powered-by {{
    font-size: 15px;
    font-weight: 500;
    color: rgba(255,255,255,0.35);
    letter-spacing: 0.08em;
    text-align: center;
  }}
</style>
</head>
<body>
  <img class="top-logo" src="data:image/png;base64,{white_logo}" alt="Genius Money">

  <div class="section">
    <div class="who-label">April 2026 Deadline</div>
    <div class="who-headline">Who Needs<br>MTD?</div>

    <div class="bullet-list">
      <div class="bullet">
        <div class="bullet-icon">✓</div>
        <div class="bullet-text">Self-employed earners</div>
      </div>
      <div class="bullet">
        <div class="bullet-icon">✓</div>
        <div class="bullet-text">Landlords with rental income</div>
      </div>
      <div class="bullet">
        <div class="bullet-icon">✓</div>
        <div class="bullet-text">Income over £50,000</div>
      </div>
      <div class="bullet">
        <div class="bullet-icon">✓</div>
        <div class="bullet-text">Filing self-assessment returns</div>
      </div>
    </div>
  </div>

  <div class="pink-divider"></div>

  <div class="section" style="display:flex;flex-direction:column;align-items:center;">
    <div class="get-sorted-label">Get sorted from</div>
    <div class="big-price">£199/YEAR</div>
    <div class="signup-btn">geniustax.co.uk/signup</div>
  </div>

  <div class="spacer"></div>

  <div class="powered-by">Powered by Genius Money</div>
</body>
</html>"""


# ─────────────────────────────────────────────
# RENDER WITH PLAYWRIGHT
# ─────────────────────────────────────────────
images = [
    ("v2-countdown-square.png",   html_1, 1080, 1080),
    ("v2-earlybird-square.png",   html_2, 1080, 1080),
    ("v2-mtd-linkedin.png",       html_3, 1200, 630),
    ("v2-story-whoneeds.png",     html_4, 1080, 1920),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for filename, html_content, width, height in images:
        print(f"Rendering {filename} ({width}x{height})...")
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html_content)
        page.wait_for_timeout(2500)  # wait for Google Fonts
        out_path = OUTPUT_DIR / filename
        page.screenshot(path=str(out_path), full_page=False)
        size_kb = out_path.stat().st_size // 1024
        print(f"  ✓ Saved: {out_path} ({size_kb} KB)")
        page.close()
    browser.close()

print("\nAll 4 images rendered successfully.")
