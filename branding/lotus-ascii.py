#!/usr/bin/env python3
"""MindOS lotus ASCII logosu (elle çizim, simetrik).

Sol yarı elle çizilir; sağ yarı otomatik aynalanır. Renkler:
  1 = dış kontur (koyu mavi), 2 = iç çizgiler / sap (açık mavi)
Çıktılar:
  logo.txt           -> fastfetch ($1/$2 yer tutucuları)
  neofetch-ascii.txt -> neofetch (${c1}/${c2} yer tutucuları)
  logo-preview.png   -> önizleme
"""
import sys
from PIL import Image, ImageDraw, ImageFont

# Sol yarı koordinatlarla çizilir (satır, sütun, metin, renk); sağ yarı aynalanır.
# Eksen sütun 21|22 arasında. Renk 1 = dış kontur, 2 = iç çizgi / sap.
ROWS, HALF = 18, 22
STROKES = [
    # üst yaprak (sivri uç -> merkez)
    (0, 21, "/", 1), (1, 20, "/", 1), (2, 19, "/", 1), (3, 18, "/", 1),
    (4, 17, "|", 1), (5, 17, "|", 1), (6, 17, "|", 1),
    (7, 18, "\\", 2), (8, 19, "\\", 2), (9, 20, "\\", 2), (10, 21, "\\", 2),
    # sol üst yaprak: sol üst köşe, üst kenar, dikey sol kenar
    (2, 5, ".", 1), (2, 6, "________", 1), (3, 14, "`-.", 1),
    (3, 5, "|", 1), (4, 5, "|", 1), (5, 5, "|", 1), (6, 5, "|", 1),
    # sol orta yaprak: dış kenarlar ve uç
    (7, 2, "__.", 1), (7, 5, "|", 1), (8, 0, ".-'", 1), (9, 0, "<", 1),
    (10, 1, "`-._", 1), (11, 5, "`-.", 1),
    # orta yaprağın merkeze giden iç çizgileri
    (8, 5, "`-.__", 2), (9, 10, "`--.__", 2), (10, 16, "`--.", 2),
    (11, 8, "`--.____", 2), (11, 16, "___", 2),
    # sol alt yaprak: sol kenar, alt kenar, merkeze çıkan sağ kenar
    (12, 6, "|", 1), (13, 6, "|", 1), (14, 6, "|", 1), (15, 6, "|", 1),
    (16, 6, "|_________", 1), (16, 16, "/", 1), (15, 17, "/", 1), (14, 18, "/", 1),
    (13, 19, "/", 1), (12, 20, "/", 1),
    # sap
    (11, 21, "|", 2), (12, 21, "|", 2), (13, 21, "|", 2), (14, 21, "|", 2), (15, 21, "|", 2),
    (16, 21, "|", 2), (17, 21, "|", 2),
]


def build_left():
    grid = [[" "] * HALF for _ in range(ROWS)]
    mask = [[" "] * HALF for _ in range(ROWS)]
    for r, c, text, col in STROKES:
        for k, ch in enumerate(text):
            if 0 <= c + k < HALF:
                grid[r][c + k] = ch
                mask[r][c + k] = "2" if col == 2 else " "
    return ["".join(g) for g in grid], ["".join(m) for m in mask]


LEFT, MASK = build_left()

MIRROR = str.maketrans("/\\()<>[]{}`'", "\\/)(><][}{'`")


def full_lines():
    out = []
    for left, mask in zip(LEFT, MASK):
        left = left[:22].ljust(22)
        mask = mask[:22].ljust(22)
        right = left[::-1].translate(MIRROR)
        rmask = mask[::-1]
        out.append((left + right, mask + rmask))
    return out


def encode(lines, c1, c2):
    res = []
    for text, mask in lines:
        s, cur = "", None
        for ch, m in zip(text, mask):
            col = "2" if m == "2" else "1"
            if ch != " " and col != cur:
                s += c1 if col == "1" else c2
                cur = col
            s += ch
        res.append(s.rstrip())
    while res and not res[-1].strip():
        res.pop()
    return res


def render(lines, path):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
    cw, ch = 10, 20
    img = Image.new("RGB", (44 * cw + 20, len(lines) * ch + 20), (23, 25, 33))
    d = ImageDraw.Draw(img)
    colors = {"1": (30, 110, 215), "2": (120, 215, 255)}
    for i, (text, mask) in enumerate(lines):
        for j, (c, m) in enumerate(zip(text, mask)):
            if c != " ":
                d.text((10 + j * cw, 10 + i * ch), c, font=font, fill=colors["2" if m == "2" else "1"])
    img.save(path)


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    lines = full_lines()
    with open(f"{outdir}/logo.txt", "w") as f:
        f.write("\n".join(encode(lines, "$1", "$2")) + "\n")
    with open(f"{outdir}/neofetch-ascii.txt", "w") as f:
        f.write("\n".join(encode(lines, "${c1}", "${c2}")) + "\n")
    render(lines, f"{outdir}/logo-preview.png")
    for t, _ in lines:
        print(t.rstrip())
