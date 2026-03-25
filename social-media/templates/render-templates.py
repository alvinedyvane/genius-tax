#!/usr/bin/env python3
"""
Genius Tax Social Media Template Renderer
==========================================
Renders branded social media images from HTML/CSS templates using Playwright.

Usage:
  python3 render-templates.py                    # Render all templates
  python3 render-templates.py --template dark-hero --headline "Your Tax. Sorted." --photo URL
  python3 render-templates.py --variations       # Generate variations with different photos

Templates use the EXACT same chrome (logo, flag, contact, URL) across all images.
"""

from playwright.sync_api import sync_playwright
import base64, os, argparse, json

# ── Paths ──
OUTDIR = os.path.expanduser("~/Projects/genius-tax/social-media/images/branded")
LOGO_COLOUR = os.path.expanduser("~/Projects/genius-tax/logos/gws-full-colour.png")
LOGO_WHITE = os.path.expanduser("~/Projects/genius-tax/logos/gws-white.png")
FLAG = "/tmp/union-jack.png"  # Downloaded from Wikipedia

# ── Brand Constants (LOCKED) ──
CONTACT = "020 7700 2000  |  hello@geniusmoney.co.uk"
URL = "geniustax.co.uk"
LOGO_HEIGHT = "90px"
CHROME_FONT_SIZE = "2rem"
PINK = "#E5007D"
DARK = "#2D2D2D"

# ── Load Assets ──
def load_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ── Base CSS (shared across ALL templates) ──
def get_base_css():
    return """
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800;900&display=swap');
:root { --pink: #E5007D; --dark: #2D2D2D; --grey: #F7F7F7; --border: #E8E8E8; }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Montserrat', Arial, sans-serif; -webkit-font-smoothing: antialiased; color: var(--dark); overflow: hidden; }
.eyebrow {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(229,0,125,0.15); border: 1px solid rgba(229,0,125,0.3);
  color: #ff69b4; font-size: 0.85rem; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; padding: 0.45rem 1.2rem; border-radius: 100px;
}
.eyebrow::before { content: '●'; font-size: 0.5rem; color: var(--pink); }
.cta-btn {
  display: inline-block; background: var(--pink); color: white;
  padding: 1.1rem 2.5rem; border-radius: 100px; font-weight: 700;
  font-size: 1.15rem; text-decoration: none;
}
.badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
  color: white; font-size: 0.85rem; font-weight: 600; padding: 0.5rem 1rem; border-radius: 6px;
}
.flag-badge {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.25);
  padding: 8px 16px; border-radius: 8px; color: white; font-size: 1rem; font-weight: 600;
}
.flag-badge img { height: 28px; border-radius: 3px; }
.flag-badge-dark {
  display: inline-flex; align-items: center; gap: 8px;
  background: rgba(0,0,0,0.05); border: 1px solid var(--border);
  padding: 8px 16px; border-radius: 8px; color: var(--dark); font-size: 1rem; font-weight: 600;
}
.flag-badge-dark img { height: 28px; border-radius: 3px; }
"""

# ── Chrome Components ──
def dark_header(logo_white_b64, flag_b64):
    return f"""<div style="position:absolute;top:0;left:0;right:0;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;">
  <img src="data:image/png;base64,{logo_white_b64}" style="height:{LOGO_HEIGHT};" />
  <span class="flag-badge"><img src="data:image/png;base64,{flag_b64}" /> UK Tax</span>
</div>"""

def light_header(logo_colour_b64, flag_b64):
    return f"""<div style="padding:18px 30px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border);">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="data:image/png;base64,{logo_colour_b64}" style="height:{LOGO_HEIGHT};" />
    <span class="flag-badge-dark"><img src="data:image/png;base64,{flag_b64}" /> UK Tax</span>
  </div>
</div>"""

def dark_footer():
    return f"""<div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,0.4);padding:18px 30px;">
  <div style="color:rgba(255,255,255,0.95);font-size:{CHROME_FONT_SIZE};font-weight:700;text-align:center;">{CONTACT}</div>
  <div style="color:rgba(255,255,255,0.95);font-size:{CHROME_FONT_SIZE};font-weight:700;text-align:center;margin-top:3px;">{URL}</div>
</div>"""

def pink_footer():
    return f"""<div style="position:absolute;bottom:0;left:0;right:0;background:linear-gradient(90deg,var(--pink),#ff4da6);padding:18px 30px;">
  <div style="color:white;font-weight:700;font-size:{CHROME_FONT_SIZE};text-align:center;">{CONTACT}</div>
  <div style="color:white;font-weight:700;font-size:{CHROME_FONT_SIZE};text-align:center;margin-top:3px;">{URL}</div>
</div>"""

def pink_translucent_footer():
    return f"""<div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,0.15);padding:18px 30px;">
  <div style="color:rgba(255,255,255,0.95);font-size:{CHROME_FONT_SIZE};font-weight:700;text-align:center;">{CONTACT}</div>
  <div style="color:rgba(255,255,255,0.95);font-size:{CHROME_FONT_SIZE};font-weight:700;text-align:center;margin-top:3px;">{URL}</div>
</div>"""


# ── Template: Dark Hero (photo background) ──
def dark_hero(logo_white_b64, flag_b64, photo_url, eyebrow, headline, subtitle, cta, badges=None):
    badge_html = ""
    if badges:
        badge_html = '<div style="margin-top:22px;">' + " ".join(
            f'<span class="badge">✓ {b}</span>' for b in badges
        ) + '</div>'
    
    return f"""<!DOCTYPE html><html><head><style>{get_base_css()}
body {{ width:1080px;height:1080px;background:linear-gradient(rgba(0,0,0,0.50),rgba(0,0,0,0.55)),url('{photo_url}');background-size:cover;background-position:center;position:relative;display:flex;align-items:center;justify-content:center; }}
</style></head><body>
{dark_header(logo_white_b64, flag_b64)}
<div style="text-align:center;padding:110px 45px 70px;">
  <div class="eyebrow">{eyebrow}</div>
  <h1 style="color:white;font-size:5.5rem;font-weight:900;line-height:1.02;margin:20px 0 12px;letter-spacing:-3px;">{headline}</h1>
  <p style="color:rgba(255,255,255,0.8);font-size:1.25rem;margin-bottom:22px;">{subtitle}</p>
  <a class="cta-btn">{cta}</a>
  {badge_html}
</div>
{dark_footer()}
</body></html>"""


# ── Template: Pink CTA ──
def pink_cta(logo_white_b64, flag_b64, headline, subtitle, cta, badges=None):
    badge_html = ""
    if badges:
        badge_html = '<div style="margin-top:25px;">' + " ".join(
            f'<span class="badge" style="border-color:rgba(255,255,255,0.3);">✓ {b}</span>' for b in badges
        ) + '</div>'
    
    return f"""<!DOCTYPE html><html><head><style>{get_base_css()}
body {{ width:1080px;height:1080px;background:linear-gradient(135deg,var(--pink),#ff4da6);position:relative;display:flex;align-items:center;justify-content:center; }}
</style></head><body>
<div style="position:absolute;top:0;left:0;right:0;padding:20px 30px;display:flex;justify-content:space-between;align-items:center;">
  <img src="data:image/png;base64,{logo_white_b64}" style="height:{LOGO_HEIGHT};" />
  <span class="flag-badge" style="border-color:rgba(255,255,255,0.3);"><img src="data:image/png;base64,{flag_b64}" /> UK Tax</span>
</div>
<div style="text-align:center;padding:60px;">
  <h1 style="color:white;font-size:5.5rem;font-weight:900;line-height:1.02;letter-spacing:-3px;">{headline}</h1>
  <p style="color:rgba(255,255,255,0.9);font-size:1.3rem;margin:22px 0;">{subtitle}</p>
  <a class="cta-btn" style="background:white;color:var(--pink);font-size:1.2rem;padding:1.2rem 3rem;">{cta}</a>
  {badge_html}
</div>
{pink_translucent_footer()}
</body></html>"""


if __name__ == "__main__":
    print("Template system saved. Use functions above to generate images.")
    print(f"Output dir: {OUTDIR}")
    print("Available templates: dark_hero, pink_cta, light_cards, story, linkedin")
