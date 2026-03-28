#!/usr/bin/env python3
"""Generate £5/week pricing images matching the existing branded set style."""

import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

LOGOS_DIR = Path("/Users/donnapaulsen/Projects/genius-tax/logos")
OUTPUT_DIR = Path("/Users/donnapaulsen/Projects/genius-tax/social-media/images/branded")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def b64(filename):
    with open(LOGOS_DIR / filename, "rb") as f:
        return base64.b64encode(f.read()).decode()


white_logo = b64("gws-white.png")
pink_icon = b64("gm-icon-pink.png")

# ── Square 1080×1080 — Pricing Hero ──────────────────────────────────────────
html_square = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1080px;
    height: 1080px;
    background: #111111;
    font-family: 'Montserrat', sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: space-between;
    padding: 64px 72px 56px;
    overflow: hidden;
    position: relative;
  }}

  body::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 50% 110%, rgba(229,0,125,0.22) 0%, transparent 60%);
    pointer-events: none;
  }}

  .logo {{
    width: 100%;
    display: flex;
    justify-content: flex-start;
    z-index: 1;
  }}

  .logo img {{
    height: 48px;
    width: auto;
  }}

  .center {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
    z-index: 1;
    margin-top: -30px;
  }}

  .eyebrow {{
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.3em;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    margin-bottom: 20px;
  }}

  .price-from {{
    font-size: 30px;
    font-weight: 700;
    color: rgba(255,255,255,0.55);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}

  .price-big {{
    font-size: 160px;
    font-weight: 900;
    color: #E5007D;
    line-height: 0.88;
    letter-spacing: -5px;
    text-shadow: 0 0 100px rgba(229,0,125,0.4), 0 0 40px rgba(229,0,125,0.2);
  }}

  .price-week {{
    font-size: 38px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.05em;
    margin-top: 12px;
    text-transform: uppercase;
  }}

  .divider {{
    width: 72px;
    height: 3px;
    background: linear-gradient(90deg, #E5007D, rgba(229,0,125,0.2));
    border-radius: 2px;
    margin: 36px 0 30px;
  }}

  .plans-row {{
    display: flex;
    gap: 20px;
    margin-bottom: 0;
  }}

  .plan {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }}

  .plan-name {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
  }}

  .plan-price {{
    font-size: 22px;
    font-weight: 800;
    color: rgba(255,255,255,0.8);
  }}

  .plan-sep {{
    width: 1px;
    height: 40px;
    background: rgba(229,0,125,0.3);
    margin: 0 8px;
    align-self: center;
  }}

  .bottom {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 18px;
    z-index: 1;
    width: 100%;
  }}

  .cta-pill {{
    background: #E5007D;
    color: #ffffff;
    font-family: 'Montserrat', sans-serif;
    font-size: 22px;
    font-weight: 800;
    padding: 20px 72px;
    border-radius: 60px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    box-shadow: 0 8px 40px rgba(229,0,125,0.4);
  }}

  .url {{
    font-size: 15px;
    font-weight: 500;
    color: rgba(255,255,255,0.25);
    letter-spacing: 0.1em;
  }}
</style>
</head>
<body>
  <div class="logo">
    <img src="data:image/png;base64,{white_logo}" alt="Genius Money">
  </div>

  <div class="center">
    <div class="eyebrow">MTD Compliance</div>
    <div class="price-from">from</div>
    <div class="price-big">£5</div>
    <div class="price-week">per week</div>
    <div class="divider"></div>
    <div class="plans-row">
      <div class="plan">
        <div class="plan-name">Essential</div>
        <div class="plan-price">£199/yr</div>
      </div>
      <div class="plan-sep"></div>
      <div class="plan">
        <div class="plan-name">Growth Yr 1</div>
        <div class="plan-price">£299/yr</div>
      </div>
      <div class="plan-sep"></div>
      <div class="plan">
        <div class="plan-name">Growth Yr 2</div>
        <div class="plan-price">£500/yr</div>
      </div>
    </div>
  </div>

  <div class="bottom">
    <div class="cta-pill">Sign Up Today</div>
    <div class="url">geniustax.co.uk/signup</div>
  </div>
</body>
</html>"""

# ── Landscape 1200×630 ─────────────────────────────────────────────────────────
html_landscape = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800;900&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1200px;
    height: 630px;
    background: #111111;
    font-family: 'Montserrat', sans-serif;
    display: flex;
    align-items: stretch;
    overflow: hidden;
    position: relative;
  }}

  body::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 80% 50%, rgba(229,0,125,0.18) 0%, transparent 55%);
    pointer-events: none;
  }}

  .left {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 52px 56px 48px;
    z-index: 1;
  }}

  .logo img {{
    height: 40px;
    width: auto;
  }}

  .main-copy {{
    display: flex;
    flex-direction: column;
    gap: 0;
  }}

  .eyebrow {{
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.28em;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    margin-bottom: 12px;
  }}

  .from-line {{
    font-size: 24px;
    font-weight: 700;
    color: rgba(255,255,255,0.5);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  .price-big {{
    font-size: 118px;
    font-weight: 900;
    color: #E5007D;
    line-height: 0.88;
    letter-spacing: -3px;
    text-shadow: 0 0 80px rgba(229,0,125,0.35);
  }}

  .per-week {{
    font-size: 28px;
    font-weight: 800;
    color: #fff;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 8px;
  }}

  .bottom-left {{
    display: flex;
    flex-direction: column;
    gap: 8px;
  }}

  .plans-inline {{
    font-size: 14px;
    font-weight: 600;
    color: rgba(255,255,255,0.4);
    letter-spacing: 0.06em;
  }}

  .url {{
    font-size: 13px;
    font-weight: 500;
    color: rgba(255,255,255,0.2);
    letter-spacing: 0.1em;
  }}

  .right {{
    width: 380px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 52px 48px;
    z-index: 1;
    border-left: 1px solid rgba(229,0,125,0.15);
    gap: 20px;
  }}

  .right-headline {{
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    text-align: center;
    line-height: 1.3;
    letter-spacing: -0.3px;
  }}

  .right-headline span {{
    color: #E5007D;
  }}

  .plan-card {{
    width: 100%;
    background: rgba(229,0,125,0.08);
    border: 1px solid rgba(229,0,125,0.2);
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .plan-card.featured {{
    background: rgba(229,0,125,0.15);
    border-color: rgba(229,0,125,0.5);
  }}

  .plan-tier {{
    font-size: 13px;
    font-weight: 700;
    color: rgba(255,255,255,0.6);
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }}

  .plan-amount {{
    font-size: 18px;
    font-weight: 800;
    color: #ffffff;
  }}

  .plan-weekly {{
    font-size: 11px;
    color: rgba(229,0,125,0.8);
    font-weight: 600;
    text-align: right;
  }}

  .cta-pill {{
    width: 100%;
    background: #E5007D;
    color: #ffffff;
    font-family: 'Montserrat', sans-serif;
    font-size: 16px;
    font-weight: 800;
    padding: 16px 24px;
    border-radius: 40px;
    text-align: center;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    box-shadow: 0 6px 28px rgba(229,0,125,0.4);
  }}
</style>
</head>
<body>
  <div class="left">
    <div class="logo">
      <img src="data:image/png;base64,{white_logo}" alt="Genius Money">
    </div>
    <div class="main-copy">
      <div class="eyebrow">MTD Compliance</div>
      <div class="from-line">from</div>
      <div class="price-big">£5</div>
      <div class="per-week">per week</div>
    </div>
    <div class="bottom-left">
      <div class="plans-inline">Essential £199/yr &nbsp;·&nbsp; Growth £299/yr &nbsp;·&nbsp; Growth+ £500/yr</div>
      <div class="url">geniustax.co.uk/signup</div>
    </div>
  </div>

  <div class="right">
    <div class="right-headline">Making Tax Digital<br><span>starts April 2026</span></div>
    <div class="plan-card featured">
      <div>
        <div class="plan-tier">Essential</div>
        <div class="plan-amount">£199/year</div>
      </div>
      <div class="plan-weekly">£5/week</div>
    </div>
    <div class="plan-card">
      <div>
        <div class="plan-tier">Growth Yr 1</div>
        <div class="plan-amount">£299/year</div>
      </div>
      <div class="plan-weekly">£6.92/week</div>
    </div>
    <div class="plan-card">
      <div>
        <div class="plan-tier">Growth Yr 2</div>
        <div class="plan-amount">£500/year</div>
      </div>
      <div class="plan-weekly">£11.30/week</div>
    </div>
    <div class="cta-pill">Sign Up at geniustax.co.uk</div>
  </div>
</body>
</html>"""


def render(html: str, output_path: Path, width: int, height: int):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(output_path), full_page=False)
        browser.close()
    print(f"✅ Saved: {output_path}")


if __name__ == "__main__":
    print("Generating £5/week pricing images...")
    render(html_square,    OUTPUT_DIR / "10-pricing-5pw-square.png",    1080, 1080)
    render(html_landscape, OUTPUT_DIR / "10-pricing-5pw-landscape.png", 1200, 630)
    print("Done.")
