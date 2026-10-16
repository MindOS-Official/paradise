#!/usr/bin/env python3
"""MindOS Paradise fastfetch logosu: mavi lotus, libcaca ile renkli karakterlere çevrilir (Neon'daki
gibi; libcaca'nın ANSI çıktısındaki 'yanıp sön' kodları ışıltı verir). Siyah zemin terminalin kendi
arka planına bırakılır, böylece açık ve koyu terminalde aynı görünür.
kullanım: make-fastfetch-logo.py <lotus.png> <genişlik> <yükseklik> <çıktı.txt>"""
import re, subprocess, sys, tempfile
from PIL import Image
src, W, H, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
im = Image.open(src).convert("RGB")
px = im.load()
for y in range(im.size[1]):          # sıkıştırma kırıntılarını sil: zemin tam siyah olsun
    for x in range(im.size[0]):
        if max(px[x, y]) < 48:
            px[x, y] = (0, 0, 0)
with tempfile.NamedTemporaryFile(suffix=".png") as t:
    im.save(t.name)
    ans = subprocess.run(["img2txt", "-W", W, "-H", H, "--gamma=0.6", t.name],
                         capture_output=True, text=True, check=True).stdout.replace("\r", "")

def fix(m):
    codes = m.group(1).split(";")
    fg = [c for c in codes if c in {"30","31","32","33","34","35","36","37"}]
    if "40" in codes and (not fg or fg == ["30"]) and "1" not in codes:
        return "\x1b[0m"                     # siyah üstüne siyah: boşluk
    # kenarlardaki kırmızı/yeşil/sarı/mor kırıntılar mavi temaya uysun
    swap = {"31": "34", "32": "36", "33": "36", "35": "34", "40": "49"}
    return "\x1b[" + ";".join(swap.get(c, c) for c in codes) + "m"
ans = re.sub(r"\x1b\[([0-9;]*)m", fix, ans)
lines = ans.rstrip("\n").split("\n")
while lines and not re.sub(r"\x1b\[[0-9;]*m", "", lines[-1]).strip():
    lines.pop()
while lines and not re.sub(r"\x1b\[[0-9;]*m", "", lines[0]).strip():
    lines.pop(0)
open(out, "w").write("\n".join(l + "\x1b[0m" for l in lines) + "\n")
print(f"{len(lines)} satır, yanıp sönen: {ans.count(chr(27)+'[0;5;')}")
