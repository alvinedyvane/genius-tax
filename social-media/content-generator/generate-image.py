#!/usr/bin/env python3
"""
Genius Tax — Social Media Image Generator
Produces branded PNG images in three standard sizes.

Usage:
  python3 generate-image.py \
    --headline "MTD Deadline: 12 Days" \
    --subtext  "Get compliant from £299/year" \
    --slug     "mtd-countdown"
"""

import argparse
import os
import sys
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow is required. Install with: pip install Pillow")

# ── Brand constants ────────────────────────────────────────────────────────────
PINK       = (229, 0, 125)    # #E5007D
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
DARK_GREY  = (20,  20,  20)
LIGHT_PINK = (255, 200, 230)

LOGO_PATH  = Path("~/Projects/genius-tax/logos/gm-icon-outline-black.png").expanduser()
OUTPUT_DIR = Path("~/Projects/genius-tax/social-media/images").expanduser()

# (name, width, height, logo_size, logo_margin)
SIZES = [
    ("square",    1080, 1080, 120, 40),
    ("landscape", 1200,  630, 100, 36),
    ("story",     1080, 1920, 140, 50),
]


# ── Font helpers ───────────────────────────────────────────────────────────────

def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=(1 if bold else 0))
            except Exception:
                pass
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block_height(lines: list[str], font: ImageFont.FreeTypeFont,
                      spacing: int = 12) -> int:
    line_h = font.getbbox("Ag")[3] + spacing
    return line_h * len(lines)


def draw_centred_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    colour: tuple,
    centre_x: int,
    centre_y: int,
    spacing: int = 12,
) -> None:
    line_h = font.getbbox("Ag")[3] + spacing
    total_h = line_h * len(lines)
    y = centre_y - total_h // 2
    for line in lines:
        bbox = font.getbbox(line)
        x = centre_x - (bbox[2] - bbox[0]) // 2
        draw.text((x, y), line, font=font, fill=colour)
        y += line_h


def load_logo(size: tuple[int, int]) -> Image.Image | None:
    if not LOGO_PATH.exists():
        print(f"  ⚠  Logo not found at {LOGO_PATH} — skipping")
        return None
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail(size, Image.LANCZOS)
        return logo
    except Exception as e:
        print(f"  ⚠  Could not load logo: {e}")
        return None


def paste_logo(img: Image.Image, logo: Image.Image, margin: int) -> None:
    x = img.width  - logo.width  - margin
    y = img.height - logo.height - margin
    if logo.mode == "RGBA":
        img.paste(logo, (x, y), logo)
    else:
        img.paste(logo, (x, y))


# ── Decorative helpers ─────────────────────────────────────────────────────────

def draw_top_bar(draw: ImageDraw.ImageDraw, w: int, bar_h: int = 12) -> None:
    """Solid pink top bar accent."""
    draw.rectangle([0, 0, w, bar_h], fill=PINK)


def draw_pill_label(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    bg: tuple,
    fg: tuple,
    pad_x: int = 28,
    pad_y: int = 14,
) -> tuple[int, int]:
    """Draw a rounded pill and return (width, height)."""
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pill_w, pill_h = tw + pad_x * 2, th + pad_y * 2
    r = pill_h // 2
    draw.rounded_rectangle([x, y, x + pill_w, y + pill_h], radius=r, fill=bg)
    draw.text((x + pad_x, y + pad_y), text, font=font, fill=fg)
    return pill_w, pill_h


def days_until_mtd() -> int:
    deadline = date(2026, 4, 6)
    return max(0, (deadline - date.today()).days)


# ── Per-size renderers ─────────────────────────────────────────────────────────

def render_square(headline: str, subtext: str) -> Image.Image:
    """1080×1080 — Instagram / Facebook feed post."""
    W, H = 1080, 1080
    img  = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # Pink top half
    draw.rectangle([0, 0, W, H // 2], fill=PINK)
    draw_top_bar(draw, W, 14)

    # Headline (white on pink)
    font_h = load_font(88, bold=True)
    h_lines = wrap_text(headline, font_h, W - 100)
    draw_centred_block(draw, h_lines, font_h, WHITE, W // 2, H // 4)

    # Divider
    draw.rectangle([60, H // 2 - 3, W - 60, H // 2 + 3], fill=PINK)

    # Subtext (dark on white)
    font_s = load_font(56)
    s_lines = wrap_text(subtext, font_s, W - 120)
    draw_centred_block(draw, s_lines, font_s, DARK_GREY, W // 2, H * 3 // 4 - 40)

    # Days badge
    days = days_until_mtd()
    font_badge = load_font(34)
    badge_txt = f"{days} days to MTD · 6 Apr 2026"
    draw_centred_block(draw, [badge_txt], font_badge, PINK, W // 2, H * 3 // 4 + 100)

    # URL
    font_url = load_font(36)
    draw_centred_block(draw, ["geniustax.co.uk"], font_url, (160, 160, 160), W // 2, H - 80)

    return img


def render_landscape(headline: str, subtext: str) -> Image.Image:
    """1200×630 — LinkedIn / Twitter / Open Graph."""
    W, H = 1200, 630
    img  = Image.new("RGB", (W, H), DARK_GREY)
    draw = ImageDraw.Draw(img)

    # Pink left strip
    strip_w = 14
    draw.rectangle([0, 0, strip_w, H], fill=PINK)

    # Pink right column
    col_w = W // 3
    draw.rectangle([W - col_w, 0, W, H], fill=PINK)

    # Headline (left side, white on dark)
    font_h = load_font(72, bold=True)
    h_lines = wrap_text(headline, font_h, W - col_w - 100)
    draw_centred_block(draw, h_lines, font_h, WHITE,
                       (W - col_w) // 2, H // 2 - 50)

    # Subtext below headline
    font_s = load_font(40)
    s_lines = wrap_text(subtext, font_s, W - col_w - 100)
    sub_h = text_block_height(h_lines, font_h) // 2 + text_block_height(s_lines, font_s) // 2 + 30
    draw_centred_block(draw, s_lines, font_s, LIGHT_PINK,
                       (W - col_w) // 2, H // 2 + sub_h)

    # Right column content
    days = days_until_mtd()
    font_num  = load_font(120, bold=True)
    font_days = load_font(42,  bold=True)
    font_sub2 = load_font(32)

    cx = W - col_w // 2
    num_bbox = font_num.getbbox(str(days))
    draw.text((cx - (num_bbox[2] - num_bbox[0]) // 2, H // 2 - 140),
              str(days), font=font_num, fill=WHITE)
    draw_centred_block(draw, ["DAYS LEFT"], font_days, WHITE, cx, H // 2 + 10)
    draw_centred_block(draw, ["to MTD deadline"], font_sub2, (255, 180, 220), cx, H // 2 + 80)

    # URL bottom left
    font_url = load_font(30)
    draw.text((strip_w + 24, H - 50), "geniustax.co.uk/signup",
              font=font_url, fill=(180, 180, 180))

    return img


def render_story(headline: str, subtext: str) -> Image.Image:
    """1080×1920 — Instagram / TikTok story."""
    W, H = 1080, 1920
    img  = Image.new("RGB", (W, H), PINK)
    draw = ImageDraw.Draw(img)

    # Top safe-zone label
    font_label = load_font(40)
    draw_centred_block(draw, ["MAKING TAX DIGITAL"], font_label,
                       (255, 180, 220), W // 2, 120)

    # Countdown
    days = days_until_mtd()
    font_num  = load_font(200, bold=True)
    font_days = load_font(64,  bold=True)
    num_str   = str(days)
    num_bbox  = font_num.getbbox(num_str)
    draw.text(((W - (num_bbox[2] - num_bbox[0])) // 2, H // 2 - 420),
              num_str, font=font_num, fill=WHITE)
    draw_centred_block(draw, ["DAYS"], font_days, WHITE, W // 2, H // 2 - 180)

    # White card in the middle
    card_margin = 60
    card_top    = H // 2 - 80
    card_bottom = H // 2 + 440
    r = 40
    draw.rounded_rectangle(
        [card_margin, card_top, W - card_margin, card_bottom],
        radius=r, fill=WHITE
    )

    # Headline on card (pink)
    font_h  = load_font(72, bold=True)
    font_s  = load_font(52)
    h_lines = wrap_text(headline, font_h, W - card_margin * 2 - 60)
    draw_centred_block(draw, h_lines, font_h, PINK, W // 2,
                       card_top + 100 + text_block_height(h_lines, font_h) // 2)

    # Subtext on card
    s_lines = wrap_text(subtext, font_s, W - card_margin * 2 - 60)
    card_mid_y = (card_top + card_bottom) // 2 + 80
    draw_centred_block(draw, s_lines, font_s, DARK_GREY, W // 2, card_mid_y)

    # CTA pill at bottom of card
    font_cta = load_font(44, bold=True)
    cta_text  = "geniustax.co.uk/signup"
    cta_bbox  = font_cta.getbbox(cta_text)
    cta_w     = cta_bbox[2] - cta_bbox[0]
    pill_x    = (W - cta_w - 80) // 2
    pill_y    = card_bottom - 100
    draw_pill_label(draw, cta_text, font_cta, pill_x, pill_y, PINK, WHITE, 40, 18)

    # Bottom disclaimer
    font_disc = load_font(36)
    draw_centred_block(draw, ["April 6, 2026 · Be ready."],
                       font_disc, (255, 200, 230), W // 2, H - 120)

    return img


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Genius Tax social image generator")
    parser.add_argument("--headline", required=True, help="Main headline text")
    parser.add_argument("--subtext",  required=True, help="Supporting subtext")
    parser.add_argument("--slug",     required=True, help="URL-safe slug for filenames")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    today = date.today().strftime("%Y-%m-%d")

    print(f"🎨  Genius Tax Image Generator")
    print(f"    Headline : {args.headline}")
    print(f"    Subtext  : {args.subtext}")
    print()

    renderers = {
        "square":    render_square,
        "landscape": render_landscape,
        "story":     render_story,
    }

    for name, renderer in renderers.items():
        # Find size config for logo
        cfg = next((s for s in SIZES if s[0] == name), None)
        logo_size   = (cfg[3], cfg[3]) if cfg else (120, 120)
        logo_margin = cfg[4]            if cfg else 40

        print(f"  Rendering {name} …", end=" ", flush=True)
        img  = renderer(args.headline, args.subtext)
        logo = load_logo(logo_size)
        if logo:
            paste_logo(img, logo, logo_margin)

        out_path = OUTPUT_DIR / f"{today}-{args.slug}-{name}.png"
        img.save(out_path, "PNG", optimize=True)
        print(f"→ {out_path.name}")

    print(f"\n✅  All images saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
