#!/usr/bin/env python3
"""MindOS Paradise duvar kağıdı: lotus deseni, vektör olarak istenen çözünürlükte çizilir.

kullanım: make-wallpaper.py <çıktı.jpg|png> [genişlik] [yükseklik]
"""
import math
import random
import sys

import cairo
from PIL import Image, ImageFilter

OUT = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 3840
H = int(sys.argv[3]) if len(sys.argv) > 3 else 2160
S = H / 654 * 0.72  # orijinal 1170x654 tasarımdan biraz daha sık desen

BG_TOP = (0.800, 0.925, 0.930)
BG_BOTTOM = (0.700, 0.875, 0.890)
FILL = (0.365, 0.745, 0.905)
STROKE = (0.135, 0.435, 0.700)
INNER = (0.270, 0.600, 0.820)
SMALL = (0.560, 0.785, 0.865)

# (açı derece, boy, genişlik) - açı dikeyden saat yönünde
PETALS = [(-126, 0.84, 0.27), (126, 0.84, 0.27), (-87, 0.98, 0.26), (87, 0.98, 0.26),
          (-47, 1.0, 0.26), (47, 1.0, 0.26), (0, 1.0, 0.27)]


def petal_path(ctx, length, half_w, shrink=1.0):
    """Tabanı (0,0)'da, yukarı bakan sivri uçlu yaprak"""
    L, w = length * shrink, half_w * shrink
    oy = -length * 0.5 * (1 - shrink)  # iç çizgi yaprağın ortasına doğru küçülür
    pts = lambda x, y: (x, y + oy)
    ctx.move_to(*pts(0, -L * 0.02))
    ctx.curve_to(*pts(-w * 0.18, -L * 0.10), *pts(-w * 0.98, -L * 0.30), *pts(-w * 1.0, -L * 0.57))
    ctx.curve_to(*pts(-w * 1.0, -L * 0.79), *pts(-w * 0.16, -L * 0.85), *pts(0, -L))
    ctx.curve_to(*pts(w * 0.16, -L * 0.85), *pts(w * 1.0, -L * 0.79), *pts(w * 1.0, -L * 0.57))
    ctx.curve_to(*pts(w * 0.98, -L * 0.30), *pts(w * 0.18, -L * 0.10), *pts(0, -L * 0.02))
    ctx.close_path()


def each_petal(ctx, cx, cy, size, fn):
    for ang, ln, wd in PETALS:
        ctx.save()
        ctx.translate(cx, cy)
        ctx.rotate(math.radians(ang))
        fn(size * ln, size * ln * wd)
        ctx.restore()


def stem_path(ctx, cx, cy, size):
    sw = size * 0.055
    ctx.move_to(cx - sw, cy + size * 0.06)
    ctx.line_to(cx - sw, cy + size * 0.66)
    ctx.arc_negative(cx, cy + size * 0.66, sw, math.pi, 0)
    ctx.line_to(cx + sw, cy + size * 0.06)
    ctx.arc_negative(cx, cy + size * 0.06, sw, 0, math.pi)
    ctx.close_path()


def big_lotus(ctx, cx, cy, size):
    lw = size * 0.019
    # sap
    stem_path(ctx, cx, cy, size)
    ctx.set_source_rgb(*FILL)
    ctx.fill_preserve()
    ctx.set_source_rgb(*STROKE)
    ctx.set_line_width(lw)
    ctx.stroke()

    # 1) tüm yaprakların dolgusu, 2) üst üste binen tüm konturlar görünür
    def fill(L, w):
        petal_path(ctx, L, w)
        ctx.set_source_rgb(*FILL)
        ctx.fill()

    def outline(L, w):
        petal_path(ctx, L, w)
        ctx.set_source_rgb(*STROKE)
        ctx.set_line_width(lw)
        ctx.stroke()
        petal_path(ctx, L, w, shrink=0.90)
        ctx.set_source_rgba(*INNER, 0.85)
        ctx.set_line_width(lw * 0.45)
        ctx.stroke()

    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    each_petal(ctx, cx, cy, size, fill)
    each_petal(ctx, cx, cy, size, outline)


def small_lotus(ctx, cx, cy, size):
    ctx.push_group()
    stem_path(ctx, cx, cy, size)
    ctx.set_source_rgb(*SMALL)
    ctx.fill()

    def fill(L, w):
        petal_path(ctx, L, w)
        ctx.set_source_rgb(*SMALL)
        ctx.fill()

    def outline(L, w):
        petal_path(ctx, L, w)
        ctx.set_source_rgba(1, 1, 1, 0.35)
        ctx.set_line_width(size * 0.018)
        ctx.stroke()

    each_petal(ctx, cx, cy, size, fill)
    each_petal(ctx, cx, cy, size, outline)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(0.85)


def background():
    """Yumuşak dikey geçiş + hafif sulu boya dokusu"""
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, W * 0.25, H)
    g.add_color_stop_rgb(0, *BG_TOP)
    g.add_color_stop_rgb(1, *BG_BOTTOM)
    ctx.set_source(g)
    ctx.paint()
    img = Image.frombuffer("RGBA", (W, H), bytes(surf.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
    rnd = random.Random(12)
    noise = Image.new("L", (48, 27))
    noise.putdata([rnd.randint(0, 255) for _ in range(48 * 27)])
    noise = noise.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(H / 60))
    light = Image.new("RGB", (W, H), (236, 248, 248))
    return Image.composite(light, img, noise.point(lambda v: int(v * 0.22)))


bg = background()
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
ctx.set_antialias(cairo.ANTIALIAS_BEST)

big = 123 * S          # yaprak boyu
dx, dy = 400 * S, 193 * S
ox, oy = (W - 1170 * S) / 2 + 185 * S, 130 * S
rows = range(-2, int(H / dy) + 3)
cols = range(-3, int(W / dx) + 4)
for r in rows:
    for c in cols:
        shift = 0 if r % 2 else dx / 2
        x = ox + c * dx + shift
        y = oy + r * dy
        small_lotus(ctx, x + dx / 2, y + 12 * S, big * 0.48)
for r in rows:
    for c in cols:
        shift = 0 if r % 2 else dx / 2
        big_lotus(ctx, ox + c * dx + shift, oy + r * dy, big)

# cairo önceden çarpılmış (premultiplied) alfa kullanır
fg = Image.frombuffer("RGBa", (W, H), bytes(surf.get_data()), "raw", "BGRa", 0, 1).convert("RGBA")
bg = bg.convert("RGBA")
bg.alpha_composite(fg)
out = bg.convert("RGB")
if OUT.lower().endswith((".jpg", ".jpeg")):
    out.save(OUT, quality=93, subsampling=0, optimize=True)
else:
    out.save(OUT, optimize=True)
print(OUT, out.size)
