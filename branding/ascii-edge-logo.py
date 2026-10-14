#!/usr/bin/env python3
"""MindOS lotus logosundan kenar tabanlı (kontur) renkli ASCII logo üretir.

Yaprak sınırları (dış silüet + üst üste binen yaprakların iç çizgileri) algılanır,
her karakter hücresi için çizginin yönüne göre / \\ | _ - karakteri seçilir.
Dış kontur $1 (koyu mavi), iç çizgiler ve sap $2 (açık mavi) ile renklenir.

kullanım: ascii-edge-logo.py <logo.png> <çıktı_öneki> [sütun]
çıktı: <önek>.tmpl  (renk yer tutucusu ${C1}/${C2})  ve  <önek>.png önizleme
"""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

src, out = sys.argv[1], sys.argv[2]
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 40
ASPECT = 2.1  # terminal hücresi yükseklik/genişlik

im = Image.open(src).convert("L").filter(ImageFilter.GaussianBlur(1.2))
L = np.asarray(im, dtype=np.float32)
fg = L > 60                                   # logo (yaprak + sap)
ys, xs = np.nonzero(fg)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
pad = 6
L = L[max(y0 - pad, 0):y1 + pad, max(x0 - pad, 0):x1 + pad]
fg = L > 60
H, W = L.shape

gy, gx = np.gradient(L)
mag = np.hypot(gx, gy)
edge = mag > 6.0

ROWS = round(COLS * H / W / ASPECT)
cw, ch = W / COLS, H / ROWS


def pick_char(sel_gx, sel_gy, ys_in_cell):
    # yapı tensörü ile baskın kenar yönü
    jxx, jyy, jxy = (sel_gx ** 2).sum(), (sel_gy ** 2).sum(), (sel_gx * sel_gy).sum()
    grad_ang = 0.5 * math.atan2(2 * jxy, jxx - jyy)          # gradyan yönü
    edge_ang = math.degrees(grad_ang + math.pi / 2) % 180     # kenar yönü (görüntü koordinatı, y aşağı)
    # görüntüde y aşağı doğru -> ekranda '/' kenarı ~135°, '\\' ~45°
    if edge_ang < 22.5 or edge_ang >= 157.5:
        return "_" if ys_in_cell.mean() > 0.55 else "-"
    if edge_ang < 67.5:
        return "\\"
    if edge_ang < 112.5:
        return "|"
    return "/"


lines = []
for r in range(ROWS):
    line, cur = "", None
    for c in range(COLS):
        ya, yb = int(r * ch), int((r + 1) * ch)
        xa, xb = int(c * cw), int((c + 1) * cw)
        e = edge[ya:yb, xa:xb]
        if e.mean() < 0.06:
            line += " "
            continue
        sel = np.nonzero(e)
        ch_ = pick_char(gx[ya:yb, xa:xb][sel], gy[ya:yb, xa:xb][sel], sel[0] / max(yb - ya, 1))
        # dış kontur: hücre arka plana değiyor mu?
        bgfrac = 1 - fg[ya:yb, xa:xb].mean()
        bright = L[ya:yb, xa:xb][fg[ya:yb, xa:xb]]
        stem = bright.size and np.percentile(bright, 90) > 235
        col = "2" if stem or bgfrac < 0.08 else "1"
        if col != cur:
            line += "${C" + col + "}"
            cur = col
        line += ch_
    lines.append(line.rstrip())
while lines and not lines[-1].replace("${C1}", "").replace("${C2}", "").strip():
    lines.pop()

with open(out + ".tmpl", "w") as f:
    f.write("\n".join(lines) + "\n")

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
cwp, chp = 10, 20
img = Image.new("RGB", (COLS * cwp + 20, len(lines) * chp + 20), (23, 25, 33))
d = ImageDraw.Draw(img)
colors = {"1": (38, 120, 220), "2": (110, 210, 255)}
for i, l in enumerate(lines):
    x, col, j = 10, "1", 0
    while j < len(l):
        if l.startswith("${C", j):
            col = l[j + 3]
            j += 5
            continue
        d.text((x, 10 + i * chp), l[j], font=font, fill=colors[col])
        x += cwp
        j += 1
img.save(out + ".png")
print(f"{COLS}x{len(lines)}")
