#!/usr/bin/env python3
"""Varsayılan kullanıcı avatarı: daireye kırpılınca düzgün görünen, kenarları tam dolu görsel.

Zemin koyu laciverten maviye çapraz geçiş; ortada lotus. GNOME (GDM, kullanıcı menüsü)
avatarı daireye kırptığı için köşelerde boşluk ya da kare çerçeve bırakılmaz.
kullanım: make-avatar.py <çıktı.png> [boyut]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

B = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 512

top, bottom = (14, 42, 92), (36, 120, 196)
bg = Image.new("RGB", (N, N))
d = ImageDraw.Draw(bg)
for y in range(N):
    for x in range(0, N, 4):
        t = min(1.0, (x + y) / (2 * N) * 1.15)
        d.rectangle([x, y, x + 3, y], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
bg = bg.convert("RGBA")
# lotusun arkasında yumuşak ışık
glow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([N * .2, N * .18, N * .8, N * .78], fill=(140, 210, 255, 90))
bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(N / 10)))

lo = Image.open(f"{B}/D12WideLogo.png").convert("RGBA")
lo = lo.crop(lo.split()[3].point(lambda v: 255 if v > 60 else 0).getbbox())
w = round(N * 0.66)
lo = lo.resize((w, round(lo.height * w / lo.width)), Image.LANCZOS)
bg.alpha_composite(lo, ((N - lo.width) // 2, (N - lo.height) // 2 + round(N * 0.01)))
bg.convert("RGB").save(out, optimize=True)
print(out, bg.size)
