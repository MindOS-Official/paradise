#!/usr/bin/env python3
"""Calamares banner: D12 lotus + sağında 'MindOS' yazısı (şeffaf arka plan)."""
import os
from PIL import Image, ImageDraw, ImageFont

B = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.environ.get("MINDOS_ROOTFS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rootfs")),
                    "usr/share/fonts/opentype/cantarell/Cantarell-VF.otf")


def lotus(path):
    im = Image.open(path).convert("RGBA")
    return im.crop(im.split()[3].point(lambda v: 255 if v > 60 else 0).getbbox())


def banner(height, color, out):
    lo = lotus(f"{B}/D12WideLogo.png")
    lh = height
    lo = lo.resize((round(lo.width * lh / lo.height), lh), Image.LANCZOS)
    font = ImageFont.truetype(FONT, round(height * 0.62))
    font.set_variation_by_axes([800])  # kalın
    tb = font.getbbox("MindOS")
    gap = round(height * 0.18)
    W = lo.width + gap + (tb[2] - tb[0]) + 4
    im = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    im.alpha_composite(lo, (0, 0))
    d = ImageDraw.Draw(im)
    # yazıyı lotusun gövdesine (dikey ortaya, biraz yukarı) hizala
    ty = (height - (tb[3] - tb[1])) // 2 - tb[1] - round(height * 0.04)
    d.text((lo.width + gap - tb[0], ty), "MindOS", font=font, fill=color)
    im.save(out)
    return im


banner(240, (7, 54, 66, 255), f"{B}/out/mindos-banner-dark.png")     # açık zemin (Calamares)
banner(240, (255, 255, 255, 255), f"{B}/out/mindos-banner-light.png")  # koyu zemin (slaytlar)
print("ok")
