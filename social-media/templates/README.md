# Social Media Image Templates

## Template System

All templates use the same chrome (header/footer) with swappable body content.

### Fixed Chrome (DO NOT CHANGE)
- **Logo**: Top-left, 90px height
- **Flag Badge**: Top-right (Union Jack + "UK Tax"), 28px flag, 1rem text
- **Footer**: Full-width bar with contact + URL at 2rem
- **Font**: Montserrat (400, 600, 700, 800, 900) via Google Fonts
- **Pink**: #E5007D
- **Dark**: #2D2D2D

### Contact Details
- Phone: 020 7700 2000
- Email: hello@geniusmoney.co.uk
- URL: geniustax.co.uk

### Dimensions
- Square (social): 1080×1080
- Story (vertical): 1080×1920
- LinkedIn (landscape): 1200×630

### Template Types

1. **dark-hero** — Photo background with dark overlay (01, 02, 06)
2. **light-cards** — Light grey/white background with card elements (03, 04, 09)
3. **pink-cta** — Full pink gradient background (07)
4. **story** — Vertical 1080×1920 with FAQ/list content (05)
5. **linkedin** — 1200×630 landscape with split layout (08)

### How to Generate Variations
1. Change the hero background image URL
2. Change the headline text
3. Change the CTA button text
4. Change the eyebrow badge text
5. Keep ALL chrome elements identical

### Hero Photo Sources (Unsplash, free commercial use)
- Current: `photo-1522202176988-66273c2fd55f` (team collaboration)
- TODO: Source more UK business/tax/construction/self-employed themed photos

### Rendering
All images rendered via Playwright (Chromium headless) from HTML/CSS.
Script: `render-templates.py`
