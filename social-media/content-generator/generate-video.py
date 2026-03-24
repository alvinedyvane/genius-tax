#!/usr/bin/env python3
"""
Genius Tax — Social Media Video Generator
Creates a 15–30 second vertical MP4 (1080×1920) with branded slides and fade transitions.

Usage:
  python3 generate-video.py \
    --message "Are you self-employed? You need MTD compliance." \
    --slug "mtd-selfemployed" \
    --pricing "£299/year"
"""

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    sys.exit("Pillow is required. Install with: pip install Pillow")

# ── Brand constants ────────────────────────────────────────────────────────────
PINK       = (229, 0, 125)       # #E5007D
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
DARK_GREY  = (20,  20,  20)

WIDTH, HEIGHT = 1080, 1920
FPS           = 30
SLIDE_SECS    = 5        # seconds each slide is held on-screen
FADE_SECS     = 0.5      # seconds for fade-in / fade-out
FADE_FRAMES   = int(FPS * FADE_SECS)

FONT_PATH = "/System/Library/Fonts/HelveticaNeue.ttc"
LOGO_PATH = Path("~/Projects/genius-tax/logos/gm-icon-outline-black.png").expanduser()

OUTPUT_DIR = Path("~/Projects/genius-tax/social-media/videos").expanduser()


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load HelveticaNeue; fall back to Helvetica then default."""
    paths = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                # index 1 tends to be Bold in the .ttc collection
                return ImageFont.truetype(p, size, index=(1 if bold else 0))
            except Exception:
                pass
    return ImageFont.load_default()


def days_until_mtd() -> int:
    """Return days from today until 6 April 2026."""
    deadline = date(2026, 4, 6)
    delta = deadline - date.today()
    return max(0, delta.days)


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Simple word-wrap: split on spaces, never exceed max_width."""
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


def draw_centred_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    colour: tuple,
    centre_y: int,
    line_spacing: int = 12,
) -> None:
    """Draw a list of lines centred horizontally, centred around centre_y."""
    line_h = font.getbbox("Ag")[3] + line_spacing
    total_h = line_h * len(lines)
    y = centre_y - total_h // 2
    for line in lines:
        bbox = font.getbbox(line)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=font, fill=colour)
        y += line_h


def load_logo(size: tuple[int, int] = (160, 160)) -> Image.Image | None:
    """Load and resize the GM logo; return None if missing."""
    if not LOGO_PATH.exists():
        print(f"  ⚠  Logo not found at {LOGO_PATH} — skipping watermark")
        return None
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo.thumbnail(size, Image.LANCZOS)
        return logo
    except Exception as e:
        print(f"  ⚠  Could not load logo: {e}")
        return None


def paste_logo(img: Image.Image, logo: Image.Image, margin: int = 48) -> None:
    """Paste the logo in the bottom-right corner with transparency support."""
    x = img.width  - logo.width  - margin
    y = img.height - logo.height - margin
    if logo.mode == "RGBA":
        img.paste(logo, (x, y), logo)
    else:
        img.paste(logo, (x, y))


# ── Slide builders ─────────────────────────────────────────────────────────────

def make_slide_1() -> Image.Image:
    """Slide 1 — 'MTD IS COMING' with countdown."""
    img  = Image.new("RGB", (WIDTH, HEIGHT), PINK)
    draw = ImageDraw.Draw(img)

    days  = days_until_mtd()
    font_big   = load_font(180, bold=True)
    font_label = load_font(72,  bold=True)
    font_sub   = load_font(52)
    font_date  = load_font(44)

    # Large countdown number
    num_str = str(days)
    bbox = font_big.getbbox(num_str)
    num_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - num_w) // 2, HEIGHT // 2 - 240), num_str,
              font=font_big, fill=WHITE)

    # "DAYS" label
    days_txt = "DAYS"
    bbox2 = font_label.getbbox(days_txt)
    draw.text(((WIDTH - (bbox2[2] - bbox2[0])) // 2, HEIGHT // 2 - 30),
              days_txt, font=font_label, fill=WHITE)

    # Subtitle
    sub_lines = wrap_text("MTD IS COMING", font_label, WIDTH - 120)
    draw_centred_text_block(draw, sub_lines, font_label, WHITE, HEIGHT // 2 + 140)

    # Date note
    date_lines = wrap_text("Making Tax Digital — 6 April 2026", font_date, WIDTH - 120)
    draw_centred_text_block(draw, date_lines, font_date, (255, 200, 230), HEIGHT // 2 + 320)

    return img


def make_slide_2(message: str) -> Image.Image:
    """Slide 2 — key message."""
    img  = Image.new("RGB", (WIDTH, HEIGHT), PINK)
    draw = ImageDraw.Draw(img)

    font_msg  = load_font(68, bold=True)
    font_tag  = load_font(44)

    lines = wrap_text(message, font_msg, WIDTH - 120)
    draw_centred_text_block(draw, lines, font_msg, WHITE, HEIGHT // 2 - 60)

    tag_lines = wrap_text("Genius Tax has you covered.", font_tag, WIDTH - 120)
    draw_centred_text_block(draw, tag_lines, font_tag, (255, 200, 230), HEIGHT // 2 + 160)

    return img


def make_slide_3(pricing: str) -> Image.Image:
    """Slide 3 — pricing."""
    img  = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(img)

    font_from   = load_font(52)
    font_price  = load_font(140, bold=True)
    font_sub    = load_font(48)

    from_lines = wrap_text("MTD-ready from just", font_from, WIDTH - 120)
    draw_centred_text_block(draw, from_lines, font_from, DARK_GREY, HEIGHT // 2 - 200)

    price_bbox = font_price.getbbox(pricing)
    draw.text(((WIDTH - (price_bbox[2] - price_bbox[0])) // 2, HEIGHT // 2 - 100),
              pricing, font=font_price, fill=PINK)

    sub_lines = wrap_text("Fully compliant. Simple. Affordable.", font_sub, WIDTH - 120)
    draw_centred_text_block(draw, sub_lines, font_sub, DARK_GREY, HEIGHT // 2 + 180)

    return img


def make_slide_4() -> Image.Image:
    """Slide 4 — CTA."""
    img  = Image.new("RGB", (WIDTH, HEIGHT), DARK_GREY)
    draw = ImageDraw.Draw(img)

    font_action = load_font(64,  bold=True)
    font_url    = load_font(68,  bold=True)
    font_sub    = load_font(44)

    action_lines = wrap_text("Get started today", font_action, WIDTH - 120)
    draw_centred_text_block(draw, action_lines, font_action, WHITE, HEIGHT // 2 - 180)

    # Pink pill background for URL
    url = "geniustax.co.uk/signup"
    url_bbox = font_url.getbbox(url)
    url_w = url_bbox[2] - url_bbox[0]
    url_h = url_bbox[3] - url_bbox[1]
    pad_x, pad_y = 60, 30
    pill_x0 = (WIDTH - url_w) // 2 - pad_x
    pill_y0 = HEIGHT // 2 - pad_y - 10
    pill_x1 = (WIDTH + url_w) // 2 + pad_x
    pill_y1 = HEIGHT // 2 + url_h + pad_y

    r = (pill_y1 - pill_y0) // 2
    draw.rounded_rectangle([pill_x0, pill_y0, pill_x1, pill_y1], radius=r, fill=PINK)
    draw.text(((WIDTH - url_w) // 2, pill_y0 + pad_y - 4),
              url, font=font_url, fill=WHITE)

    sub_lines = wrap_text("No commitment. Cancel anytime.", font_sub, WIDTH - 120)
    draw_centred_text_block(draw, sub_lines, font_sub, (180, 180, 180), HEIGHT // 2 + 240)

    return img


# ── Frame sequence builder ─────────────────────────────────────────────────────

def render_slide_frames(
    slide: Image.Image,
    logo: Image.Image | None,
    out_dir: Path,
    start_frame: int,
    total_frames: int,
) -> int:
    """
    Write PNG frames for one slide with fade-in/hold/fade-out.
    Returns the next available frame index.
    """
    # Composite logo once
    base = slide.copy()
    if logo:
        paste_logo(base, logo)

    frame_idx = start_frame
    for i in range(total_frames):
        # alpha: fade in, hold, fade out
        if i < FADE_FRAMES:
            alpha = i / FADE_FRAMES
        elif i >= total_frames - FADE_FRAMES:
            alpha = (total_frames - i) / FADE_FRAMES
        else:
            alpha = 1.0

        if alpha < 1.0:
            black = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
            frame = Image.blend(black, base, alpha)
        else:
            frame = base

        frame.save(out_dir / f"frame_{frame_idx:05d}.png")
        frame_idx += 1

    return frame_idx


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Genius Tax social video generator")
    parser.add_argument("--message", required=True,
                        help="Key message for slide 2")
    parser.add_argument("--slug",    required=True,
                        help="URL-safe slug for the output filename")
    parser.add_argument("--pricing", default="From £199/year",
                        help="Pricing string for slide 3")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    today  = date.today().strftime("%Y-%m-%d")
    output = OUTPUT_DIR / f"{today}-{args.slug}.mp4"

    print(f"🎬  Genius Tax Video Generator")
    print(f"    Message : {args.message}")
    print(f"    Pricing : {args.pricing}")
    print(f"    Output  : {output}")
    print()

    logo = load_logo()

    slides = [
        make_slide_1(),
        make_slide_2(args.message),
        make_slide_3(args.pricing),
        make_slide_4(),
    ]

    slide_frames = FPS * SLIDE_SECS  # frames per slide

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        frame_idx = 0

        for n, slide in enumerate(slides, start=1):
            print(f"  Rendering slide {n}/{len(slides)} …")
            frame_idx = render_slide_frames(slide, logo, tmp, frame_idx, slide_frames)

        total = frame_idx
        duration = total / FPS
        print(f"\n  Total frames: {total}  ({duration:.1f}s @ {FPS}fps)")
        print("  Running ffmpeg …")

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(tmp / "frame_%05d.png"),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("ffmpeg stderr:\n", result.stderr[-2000:])
            sys.exit(f"❌  ffmpeg failed (exit {result.returncode})")

    size_mb = output.stat().st_size / 1_048_576
    print(f"\n✅  Video saved → {output}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
