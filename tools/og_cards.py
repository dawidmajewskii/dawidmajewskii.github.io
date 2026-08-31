# -*- coding: utf-8 -*-
"""
og_cards.py — renders the two link-preview cards (Open Graph / Twitter Card).

Run from the project root:   python tools/og_cards.py
Reads   Img/dm-portrait-672.jpg, Img/hardware.jpg, fonts/*.ttf
Writes  Img/og-home.jpg  and  Img/og-karty.jpg   (1200x630 each)

WHY THIS SCRIPT EXISTS.
  A portfolio is shared by PASTING A LINK — into a LinkedIn message, a Slack channel, an email.
  Whatever the scraper finds behind og:image is the whole first impression, and it is shown at a
  size where the page's own typography is unreadable. Before this script there was no og:image at
  all, so the unfurl was a grey rectangle with a bare URL sitting next to everyone else's cards.

WHY NOT JUST POINT og:image AT AN EXISTING PHOTO.
  Nothing in Img/ is the right shape. Facebook, LinkedIn and Slack all lay out 1.91:1; the portrait
  is 672x896 and hardware.jpg is 1200x1600 — both PORTRAIT. A portrait source in a landscape slot
  is either letterboxed into a thumbnail or centre-cropped through the subject's face. So the cards
  are composed, not cropped.

WHY THE FONTS ARE LOADED FROM ./fonts AND NOT INSTALLED SYSTEM ONES.
  Same reason the rest of this project ships its own faces: the card must look identical no matter
  which machine renders it. Bricolage Grotesque is a VARIABLE font and Pillow cannot pick an
  instance from one, which is exactly why ./fonts holds two STATIC cuts (Display750, Head650) —
  see the comment at the top of cv.html. Those are what we use here.

PALETTE is the page's, token for token (index.html :root), so the card and the site it links to
read as one object: paper #F7F5F1, ink #16252B, muted #47595E, amber #96590E, mat #E6DFD3.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "Img")
FONTS = os.path.join(ROOT, "fonts")

W, H = 1200, 630
PAPER = (247, 245, 241)
INK = (22, 37, 43)
MUTED = (71, 89, 94)
MUTED2 = (86, 106, 110)
AMBER = (150, 89, 14)
AMBER_LINE = (176, 119, 13)
MAT = (230, 223, 211)
LINE = (205, 200, 192)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


DISPLAY = "Bricolage-Display750.ttf"
HEAD = "Bricolage-Head650.ttf"
SANS = "IBMPlexSans-Regular.ttf"
SANS_SB = "IBMPlexSans-SemiBold.ttf"
MONO = "IBMPlexMono-Medium.ttf"


def tracked(d, xy, text, f, fill, track=0):
    """Draw text with manual letter-spacing; Pillow has no tracking of its own.
    Returns the x advance, so callers can chain runs in different colours."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track
    return x


def card():
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    # the page's 64px grid, barely there — same device as body::before on the site
    for gx in range(0, W, 64):
        d.line([(gx, 0), (gx, H)], fill=(241, 237, 229), width=1)
    for gy in range(0, H, 64):
        d.line([(0, gy), (W, gy)], fill=(241, 237, 229), width=1)
    return im, d


def matted(photo, box_w, box_h, pad=14):
    """The .id-card treatment: a warm mat plus a hairline, so the head never floats
    edgeless against near-white paper. Cropped to fill, never squashed."""
    inner_w, inner_h = box_w - 2 * pad, box_h - 2 * pad
    src = photo.convert("RGB")
    scale = max(inner_w / src.width, inner_h / src.height)
    src = src.resize((max(1, round(src.width * scale)), max(1, round(src.height * scale))), Image.LANCZOS)
    left = (src.width - inner_w) // 2
    top = int((src.height - inner_h) * 0.10)          # bias UP: keep the head, drop the chest
    top = min(max(top, 0), src.height - inner_h)
    src = src.crop((left, top, left + inner_w, top + inner_h))

    plate = Image.new("RGB", (box_w, box_h), MAT)
    plate.paste(src, (pad, pad))
    pd = ImageDraw.Draw(plate)
    pd.rectangle([pad, pad, pad + inner_w - 1, pad + inner_h - 1], outline=(178, 172, 163))
    # registration corners, as on the CV and the site
    c = 26
    for cx, cy, dx, dy in ((0, 0, 1, 1), (box_w - 1, 0, -1, 1), (0, box_h - 1, 1, -1), (box_w - 1, box_h - 1, -1, -1)):
        pd.line([(cx, cy), (cx + dx * c, cy)], fill=AMBER_LINE, width=3)
        pd.line([(cx, cy), (cx, cy + dy * c)], fill=AMBER_LINE, width=3)
    return plate


# --------------------------------------------------------------- 1. og-home.jpg
im, d = card()
x = 76

tracked(d, (x, 86), "DAWIDMAJEWSKIIT.PL", font(MONO, 22), AMBER, track=3.2)

f_name = font(DISPLAY, 88)
after = tracked(d, (x, 132), "Dawid ", f_name, INK)
tracked(d, (after, 132), "Majewski", f_name, AMBER)

d.text((x, 252), "Informatyka · ERP · AI", font=font(SANS_SB, 42), fill=MUTED)

d.line([(x, 330), (x + 104, 330)], fill=AMBER_LINE, width=3)

f_small = font(SANS, 27)
for i, line in enumerate([
    "Helpdesk, infrastruktura IT i sieci — z działu IT",
    "zakładu produkcyjnego. Studia II stopnia:",
    "sztuczna inteligencja i uczenie maszynowe.",
]):
    d.text((x, 366 + i * 40), line, font=f_small, fill=MUTED)

tracked(d, (x, 516), "YOLOv8n · RASPBERRY PI 4 · PYTHON · SQL · ERP",
        font(MONO, 21), MUTED2, track=1.6)

portrait = Image.open(os.path.join(IMG, "dm-portrait-672.jpg"))
plate = matted(portrait, 330, 440)
im.paste(plate, (W - 330 - 76, (H - 440) // 2))
d.rectangle([0, H - 8, W, H], fill=AMBER_LINE)
out = os.path.join(IMG, "og-home.jpg")
im.save(out, quality=90, optimize=True, progressive=True)
print("%-24s %dx%d  %6.1f KB" % ("Img/og-home.jpg", W, H, os.path.getsize(out) / 1024))

# -------------------------------------------------------------- 2. og-karty.jpg
im, d = card()
PHOTO_W = 470
photo = Image.open(os.path.join(IMG, "hardware.jpg")).convert("RGB")
scale = max(PHOTO_W / photo.width, H / photo.height)
photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
left = (photo.width - PHOTO_W) // 2
top = (photo.height - H) // 2
photo = photo.crop((left, top, left + PHOTO_W, top + H))
im.paste(photo, (W - PHOTO_W, 0))
d.line([(W - PHOTO_W, 0), (W - PHOTO_W, H)], fill=AMBER_LINE, width=4)

x = 76
tracked(d, (x, 92), "CASE STUDY", font(MONO, 22), AMBER, track=3.2)

# Tytuł skaluje się do szczeliny między marginesem a zdjęciem. Przy sztywnym stopniu
# najdłuższy wiersz dochodził do bursztynowej krawędzi kadru i wyglądał na obcięty.
tytul = ["System rozpoznawania", "kart do gry"]
szczelina = (W - PHOTO_W) - x - 34
stopien = 60
while stopien > 34 and max(d.textlength(t, font=font(HEAD, stopien)) for t in tytul) > szczelina:
    stopien -= 2
f_t = font(HEAD, stopien)
for i, t in enumerate(tytul):
    d.text((x, 140 + i * int(stopien * 1.1)), t, font=f_t, fill=INK)

d.line([(x, 300), (x + 104, 300)], fill=AMBER_LINE, width=3)

for i, line in enumerate([
    "Wdrożenie modelu na Raspberry Pi 4 —",
    "cała inferencja lokalnie, bez chmury.",
]):
    d.text((x, 336 + i * 40), line, font=font(SANS, 27), fill=MUTED)

# the numbers are the point of this project — same four the page and the CV show
cells = [("52", "KLASY"), ("0,789", "mAP50-95"), ("~5", "FPS")]
cx = x
for val, lab in cells:
    d.rectangle([cx, 448, cx + 122, 546], fill=(241, 237, 229), outline=LINE)
    vf = font(HEAD, 38)
    d.text((cx + 61 - d.textlength(val, font=vf) / 2, 462), val, font=vf, fill=INK)
    lf = font(MONO, 16)
    tracked(d, (cx + 61 - (d.textlength(lab, font=lf) + len(lab) * 1.4) / 2, 512), lab, lf, MUTED2, track=1.4)
    cx += 134

tracked(d, (x, 570), "DAWIDMAJEWSKIIT.PL/KARTY", font(MONO, 20), MUTED2, track=2.4)

out = os.path.join(IMG, "og-karty.jpg")
im.save(out, quality=90, optimize=True, progressive=True)
print("%-24s %dx%d  %6.1f KB" % ("Img/og-karty.jpg", W, H, os.path.getsize(out) / 1024))
