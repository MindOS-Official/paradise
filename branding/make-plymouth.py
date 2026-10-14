#!/usr/bin/env python3
"""Plymouth 'mindos' teması için bgrt-fallback.png üretir.

UEFI anakartlarda açılışta firmware (anakart) logosu gösterilir; logosu olmayan
BIOS sistemlerde Plymouth bunun yerine bu görseli gösterir: yalnızca lotus logosu
(altında spinner, en altta "Powered by MindOS").
kullanım: make-plymouth.py <çıktı.png> [yükseklik]
"""
import os
import sys

from PIL import Image

B = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1]
height = int(sys.argv[2]) if len(sys.argv) > 2 else 200
im = Image.open(f"{B}/D12WideLogo.png").convert("RGBA")
im = im.crop(im.split()[3].point(lambda v: 255 if v > 60 else 0).getbbox())
im = im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
im.save(out, optimize=True)
print(out, im.size)
