# -*- coding: utf-8 -*-
"""
portrait_prep.py — one-time offline preparation of the portrait for the light theme.

Run ONCE from the project root:   python tools/portrait_prep.py
Reads   Img/Dawid_Majewski.jpg   (never modified)
Writes  Img/dm-portrait-336.{avif,webp,jpg}  and  Img/dm-portrait-672.{avif,webp,jpg}

NO BACKGROUND REMOVAL — BY DESIGN.
  An earlier version keyed the studio white to transparency so the photo could sit on the old dark
  page. That is abandoned: the hair is too fine to matte cleanly at this resolution, and on a LIGHT
  page it buys nothing anyway — a white studio background on a near-white page simply disappears.
  So the photo ships exactly as shot, opaque, and the CARD does the work of giving it an edge
  (see .id-card in index.html: a warm mat + a hairline, so the head never floats edgeless).

What this still does: a head-centred 3:4 crop, a LANCZOS downsample, and modern compression.
"""
import os
from PIL import Image

SRC = "Img/Dawid_Majewski.jpg"
OUT = "Img"
BASE = "dm-portrait"

# ---------------------------------------------------------------- 1. crop 3:4
# Source 1834x2358. 3:4 of the full height = 1768px wide.
# Head centre measured at x=949 (not the frame centre, 917), so bias the crop to the head:
# x0 = 949 - 884 = 65. Keeps every landmark (head top 6.3%, eyes 38.2%, chin 61.9%) and keeps
# the shoulders bleeding off both bottom corners.
im = Image.open(SRC).convert("RGB")
W0, H0 = im.size
CW = int(H0 * 3 / 4)                        # 1768
x0 = min(max(949 - CW // 2, 0), W0 - CW)    # 65
im = im.crop((x0, 0, x0 + CW, H0))          # 1768 x 2358
print("crop: %dx%d from %dx%d (x0=%d)" % (im.width, im.height, W0, H0, x0))

# ------------------------------------------------------ 2. export 1x and 2x, 3 formats
# Card column is 300px on desktop, capped at 320px below 860px.
# 336w covers DPR1, 672w covers DPR2. JPEG is the universal fallback (the photo is opaque
# now, so a JPEG fallback is finally free of the white-rectangle problem the alpha version had).
os.makedirs(OUT, exist_ok=True)
for w in (336, 672):
    r = im.resize((w, w * 4 // 3), Image.LANCZOS)
    for ext, kw in (("avif", dict(quality=62, speed=2)),
                    ("webp", dict(quality=86, method=6)),
                    ("jpg",  dict(quality=86, optimize=True, progressive=True))):
        p = os.path.join(OUT, "%s-%d.%s" % (BASE, w, ext))
        r.save(p, **kw)
        print("%-30s %4dx%-4d %7.1f KB" % (p, w, w * 4 // 3, os.path.getsize(p) / 1024))
