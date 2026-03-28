#!/usr/bin/env python3
"""
Pricing image v2 — matches the exact brand chrome from templates/render-templates.py.
Layout: Logo (90px) + flag badge → MAKING TAX DIGITAL headline → from £5/week → plans → contact footer.
"""

import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

LOGO_WHITE  = Path("/Users/donnapaulsen/Projects/genius-tax/logos/gws-white.png")
FLAG        = Path("/tmp/union-jack.png")
OUTDIR      = Path("/Users/donnapaulsen/Projects/genius-tax/social-media/images/branded")
OUTDIR.mkdir(parents=True, exist_ok=True)

# Brand constants — LOCKED (matches render-templates.py)
CONTACT         = "020 7700 2000  |  hello@geniusmoney.co.uk"
URL             = "geniustax.co.uk"
LOGO_HEIGHT     = "90px"
CHROME_FONT     = "2rem"
PINK            = "#E5007D"


def b64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


logo_b64 = b64(LOGO_WHITE)
flag_b64 = b64(FLAG)


BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Montserrat', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}
.flag-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.25);
  padding: 8px 16px; border-radius: 8px; color: white; font-size: 1rem; font-weight: 600;
}
.flag-badge img { height: 28px; border-radius: 3px; }
"""


# ─────────────────────────────────────────────
# SQUARE 1080×1080
# ─────────────────────────────────────────────
html_square = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
{BASE_CSS}
body {{
  width: 1080px;
  height: 1080px;
  background: #111111;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}}
body::before {{
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 100%, rgba(229,0,125,0.18) 0%, transparent 60%);
  pointer-events: none;
}}
/* Header */
.header {{
  position: absolute;
  top: 0; left: 0; right: 0;
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
/* Main content */
.main {{
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 60px;
  z-index: 1;
  gap: 0;
}}
.title {{
  font-size: 5.2rem;
  font-weight: 900;
  color: #ffffff;
  line-height: 1.0;
  letter-spacing: -3px;
  text-transform: uppercase;
  margin-bottom: 16px;
}}
.title span {{ color: {PINK}; }}
.divider {{
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, {PINK}, rgba(229,0,125,0.3));
  border-radius: 2px;
  margin: 24px 0;
}}
.from-label {{
  font-size: 1.8rem;
  font-weight: 700;
  color: rgba(255,255,255,0.5);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 4px;
}}
.price {{
  font-size: 9rem;
  font-weight: 900;
  color: {PINK};
  line-height: 0.9;
  letter-spacing: -4px;
  text-shadow: 0 0 80px rgba(229,0,125,0.35);
}}
.per-week {{
  font-size: 2.4rem;
  font-weight: 800;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-top: 10px;
  margin-bottom: 32px;
}}
.plans-row {{
  display: flex;
  gap: 0;
  border: 1px solid rgba(229,0,125,0.25);
  border-radius: 12px;
  overflow: hidden;
}}
.plan {{
  padding: 18px 28px;
  text-align: center;
  border-right: 1px solid rgba(229,0,125,0.2);
}}
.plan:last-child {{ border-right: none; }}
.plan-name {{
  font-size: 0.75rem;
  font-weight: 700;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 4px;
}}
.plan-price {{
  font-size: 1.35rem;
  font-weight: 800;
  color: rgba(255,255,255,0.85);
}}
.plan-weekly {{
  font-size: 0.8rem;
  font-weight: 600;
  color: {PINK};
  margin-top: 2px;
}}
/* Footer */
.footer {{
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: rgba(0,0,0,0.4);
  padding: 18px 30px;
  text-align: center;
}}
.footer div {{
  color: rgba(255,255,255,0.95);
  font-size: {CHROME_FONT};
  font-weight: 700;
}}
.footer div + div {{ margin-top: 3px; }}
</style></head>
<body>
  <div class="header">
    <img src="data:image/png;base64,{logo_b64}" style="height:{LOGO_HEIGHT};" />
    <span class="flag-badge">
      <img src="data:image/png;base64,{flag_b64}" /> UK Tax
    </span>
  </div>

  <div class="main">
    <div class="title">Making Tax<br><span>Digital</span></div>
    <div class="divider"></div>
    <div class="from-label">from</div>
    <div class="price">£5</div>
    <div class="per-week">per week</div>
    <div class="plans-row">
      <div class="plan">
        <div class="plan-name">Essential</div>
        <div class="plan-price">£199/yr</div>
        <div class="plan-weekly">£5/wk</div>
      </div>
      <div class="plan">
        <div class="plan-name">Growth Yr 1</div>
        <div class="plan-price">£299/yr</div>
        <div class="plan-weekly">£6.92/wk</div>
      </div>
      <div class="plan">
        <div class="plan-name">Growth Yr 2</div>
        <div class="plan-price">£500/yr</div>
        <div class="plan-weekly">£11.30/wk</div>
      </div>
    </div>
  </div>

  <div class="footer">
    <div>{CONTACT}</div>
    <div>{URL}</div>
  </div>
</body></html>"""


# ─────────────────────────────────────────────
# LANDSCAPE 1200×630
# ─────────────────────────────────────────────
html_landscape = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
{BASE_CSS}
body {{
  width: 1200px;
  height: 630px;
  background: #111111;
  position: relative;
  display: flex;
  flex-direction: column;
}}
body::before {{
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 70% 50%, rgba(229,0,125,0.16) 0%, transparent 55%);
  pointer-events: none;
}}
.header {{
  padding: 20px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}}
.body-row {{
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 50px 0 40px;
  gap: 48px;
}}
.left {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.title {{
  font-size: 3.8rem;
  font-weight: 900;
  color: #ffffff;
  line-height: 1.0;
  letter-spacing: -2px;
  text-transform: uppercase;
}}
.title span {{ color: {PINK}; }}
.divider {{
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, {PINK}, rgba(229,0,125,0.2));
  border-radius: 2px;
  margin: 14px 0;
}}
.from-label {{
  font-size: 1.2rem;
  font-weight: 700;
  color: rgba(255,255,255,0.45);
  text-transform: uppercase;
  letter-spacing: 0.15em;
}}
.price-row {{
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 2px;
}}
.price {{
  font-size: 6.5rem;
  font-weight: 900;
  color: {PINK};
  line-height: 1;
  letter-spacing: -3px;
  text-shadow: 0 0 60px rgba(229,0,125,0.3);
}}
.per-week {{
  font-size: 1.6rem;
  font-weight: 800;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}}
.right {{
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 1;
}}
.plan-card {{
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(229,0,125,0.2);
  border-radius: 10px;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.plan-card.featured {{
  background: rgba(229,0,125,0.1);
  border-color: rgba(229,0,125,0.45);
}}
.plan-left {{ display: flex; flex-direction: column; gap: 2px; }}
.plan-name {{
  font-size: 0.7rem;
  font-weight: 700;
  color: rgba(255,255,255,0.4);
  text-transform: uppercase;
  letter-spacing: 0.15em;
}}
.plan-amount {{
  font-size: 1.2rem;
  font-weight: 800;
  color: #ffffff;
}}
.plan-weekly {{
  font-size: 0.85rem;
  font-weight: 700;
  color: {PINK};
}}
.footer {{
  flex-shrink: 0;
  background: rgba(0,0,0,0.4);
  padding: 14px 30px;
  text-align: center;
}}
.footer div {{
  color: rgba(255,255,255,0.95);
  font-size: {CHROME_FONT};
  font-weight: 700;
  display: inline;
}}
.footer .sep {{ color: rgba(255,255,255,0.3); margin: 0 12px; }}
</style></head>
<body>
  <div class="header">
    <img src="data:image/png;base64,{logo_b64}" style="height:{LOGO_HEIGHT};" />
    <span class="flag-badge">
      <img src="data:image/png;base64,{flag_b64}" /> UK Tax
    </span>
  </div>

  <div class="body-row">
    <div class="left">
      <div class="title">Making Tax<br><span>Digital</span></div>
      <div class="divider"></div>
      <div class="from-label">from</div>
      <div class="price-row">
        <div class="price">£5</div>
        <div class="per-week">per week</div>
      </div>
    </div>

    <div class="right">
      <div class="plan-card featured">
        <div class="plan-left">
          <div class="plan-name">Essential</div>
          <div class="plan-amount">£199 / year</div>
        </div>
        <div class="plan-weekly">£5 / week</div>
      </div>
      <div class="plan-card">
        <div class="plan-left">
          <div class="plan-name">Growth — Year 1</div>
          <div class="plan-amount">£299 / year</div>
        </div>
        <div class="plan-weekly">£6.92 / week</div>
      </div>
      <div class="plan-card">
        <div class="plan-left">
          <div class="plan-name">Growth — Year 2</div>
          <div class="plan-amount">£500 / year</div>
        </div>
        <div class="plan-weekly">£11.30 / week</div>
      </div>
    </div>
  </div>

  <div class="footer">
    <div>{CONTACT}</div>
    <span class="sep">|</span>
    <div>{URL}</div>
  </div>
</body></html>"""


def render(html: str, out: Path, w: int, h: int):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(out), full_page=False)
        browser.close()
    print(f"✅  {out.name}")


if __name__ == "__main__":
    print("Generating pricing images v2 (brand-matched)...")
    render(html_square,    OUTDIR / "10-pricing-5pw-square.png",    1080, 1080)
    render(html_landscape, OUTDIR / "10-pricing-5pw-landscape.png", 1200, 630)
    print("Done.")
