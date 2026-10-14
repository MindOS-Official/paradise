#!/usr/bin/env python3
"""MindOS lotus logosundan renkli ASCII/braille logo üretir + önizleme render eder.
Renk yer tutucuları: fastfetch için $1/$2, neofetch için ${c1}/${c2}."""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1]
OUT = sys.argv[2]          # çıktı öneki
COLS = int(sys.argv[3]) if len(sys.argv) > 3 else 38

im = Image.open(SRC).convert("RGBA")
bbox = im.split()[3].point(lambda a: 255 if a > 40 else 0).getbbox()
im = im.crop(bbox)
bg = Image.new("RGBA", im.size, (255, 255, 255, 0))
alpha = im.split()[3]
rgb = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("RGB")


def cell_stats(img, a, x0, y0, x1, y1):
    n = cov = dark = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            n += 1
            if a.getpixel((x, y)) > 100:
                cov += 1
                r, g, b = img.getpixel((x, y))
                if (r + g + b) / 3 < 120:     # koyu mavi kontur
                    dark += 1
    return cov / max(n, 1), dark / max(cov, 1)


def ramp_logo(cols):
    rows = round(cols * im.height / im.width / 2.05)
    cw, ch = im.width / cols, im.height / rows
    ramp = " .:-=+*#%@"
    lines = []
    for r in range(rows):
        line, cur = "", None
        for c in range(cols):
            x0, y0 = int(c * cw), int(r * ch)
            x1, y1 = max(int((c + 1) * cw), x0 + 1), max(int((r + 1) * ch), y0 + 1)
            cov, dark = cell_stats(rgb, alpha, x0, y0, x1, y1)
            if cov < 0.12:
                line += " "
                continue
            col = "1" if dark > 0.30 else "2"
            chr_ = ramp[min(len(ramp) - 1, int(cov * (len(ramp) - 1) + 0.5))] if col == "2" else "#" if cov > .5 else "*"
            if col != cur:
                line += "${C" + col + "}"
                cur = col
            line += chr_
        lines.append(line.rstrip())
    return lines


def braille_logo(cols):
    rows = round(cols * im.height / im.width / 2.05)
    W, H = cols * 2, rows * 4
    a = alpha.resize((W, H), Image.LANCZOS)
    small = rgb.resize((W, H), Image.LANCZOS)
    bits = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]
    lines = []
    for r in range(rows):
        line, cur = "", None
        for c in range(cols):
            code, dark, on = 0, 0, 0
            for dx, dy, bit in bits:
                x, y = c * 2 + dx, r * 4 + dy
                if a.getpixel((x, y)) > 110:
                    code |= bit
                    on += 1
                    if sum(small.getpixel((x, y))) / 3 < 140:
                        dark += 1
            if not code:
                line += " "
                continue
            col = "1" if dark * 2 >= on else "2"
            if col != cur:
                line += "${C" + col + "}"
                cur = col
            line += chr(0x2800 + code)
        lines.append(line.rstrip())
    return lines


def render(lines, path):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    cw, ch = 10, 19
    W = max(len(l.replace("${C1}", "").replace("${C2}", "")) for l in lines) * cw + 20
    img = Image.new("RGB", (W, len(lines) * ch + 20), (23, 25, 33))
    d = ImageDraw.Draw(img)
    colors = {"1": (38, 139, 210), "2": (100, 215, 255)}
    for i, l in enumerate(lines):
        x, col, j = 10, "1", 0
        while j < len(l):
            if l.startswith("${C", j):
                col = l[j + 3]; j += 5; continue
            d.text((x, 10 + i * ch), l[j], font=font, fill=colors[col]); x += cw; j += 1
    img.save(path)


for name, fn in (("ramp", ramp_logo), ("braille", braille_logo)):
    lines = fn(COLS)
    with open(f"{OUT}-{name}.tmpl", "w") as f:
        f.write("\n".join(lines) + "\n")
    render(lines, f"{OUT}-{name}.png")
    print(name, len(lines), "satır")
