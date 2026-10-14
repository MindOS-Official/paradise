#!/usr/bin/env python3
"""MindOS ikonları: ArcMenu düğmesi (D12, şeffaf) ve Mind Arc uygulama ikonu (dolgun, kare)."""
import os
from PIL import Image, ImageDraw, ImageFilter

B = os.path.dirname(os.path.abspath(__file__))


def lotus(path):
    im = Image.open(path).convert("RGBA")
    a = im.split()[3].point(lambda v: 255 if v > 60 else 0)
    return im.crop(a.getbbox())


def square(im, size, fill=0.94):
    """Lotusu şeffaf kare tuvalin ortasına, kenarlara yakın büyüklükte yerleştirir"""
    scale = fill * size / max(im.size)
    lo = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(lo, ((size - lo.width) // 2, (size - lo.height) // 2))
    return out


def app_icon(im, size=512):
    """Koyu mavi gradyanlı yuvarlatılmış kare + parlayan büyük lotus"""
    S = size * 4  # süper örnekleme ile pürüzsüz kenarlar
    bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    grad = Image.new("RGBA", (S, S))
    top, bottom = (24, 58, 112), (6, 18, 44)
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        t = y / (S - 1)
        gd.line([(0, y), (S, y)], fill=tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,))
    margin = round(S * 0.06)
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([margin, margin, S - margin, S - margin], radius=round(S * 0.22), fill=255)
    bg.paste(grad, (0, 0), mask)
    # ince açık kenar çizgisi
    ImageDraw.Draw(bg).rounded_rectangle([margin, margin, S - margin, S - margin], radius=round(S * 0.22),
                                         outline=(120, 190, 255, 90), width=round(S * 0.006))
    lo = square(im, S, fill=0.80)
    glow = lo.split()[3].filter(ImageFilter.GaussianBlur(S * 0.03))
    glow_layer = Image.new("RGBA", (S, S), (80, 180, 255, 0))
    glow_layer.putalpha(glow.point(lambda v: v * 0.55))
    bg.alpha_composite(glow_layer)
    bg.alpha_composite(lo, (0, round(S * 0.01)))
    return bg.resize((size, size), Image.LANCZOS)


d12 = lotus(f"{B}/D12logo.png")
wide = lotus(f"{B}/D12WideLogo.png")
os.makedirs(f"{B}/out", exist_ok=True)
square(d12, 256, 0.98).save(f"{B}/out/mindos-d12.png")
icon = app_icon(wide, 512)
icon.save(f"{B}/out/mind-arc-512.png")
for s in (256, 128, 64, 48, 32, 24, 16):
    icon.resize((s, s), Image.LANCZOS).save(f"{B}/out/mind-arc-{s}.png")
print("tamam")
