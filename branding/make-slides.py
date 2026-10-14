#!/usr/bin/env python3
"""Calamares slayt görselleri (metinler QML'de, iki dilli).

Ekran görüntüleri QEMU testlerinden alınır; pencere bölgesi kırpılır,
yuvarlatılmış köşe + yumuşak gölge ile Solarized açık zemine oturtulur.
kullanım: make-slides.py <ekran_görüntüsü_dizini> <çıktı_dizini>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SHOTS, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
B = os.path.dirname(os.path.abspath(__file__))
W, H = 720, 400
BG = (253, 246, 227)  # Solarized base3 (Calamares zemini)
FONT = os.path.join(os.environ.get("MINDOS_ROOTFS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rootfs")),
                    "usr/share/fonts/opentype/cantarell/Cantarell-VF.otf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def framed(img, max_w=660, max_h=360, radius=14):
    """Görseli yuvarlatılmış köşeli, gölgeli bir karta yerleştirir"""
    img = img.convert("RGBA")
    img.thumbnail((max_w, max_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), BG + (255,))
    x, y = (W - img.width) // 2, (H - img.height) // 2
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x + 2, y + 6, x + img.width + 2, y + img.height + 6],
                                             radius=radius, fill=(7, 54, 66, 70))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=radius, fill=255)
    canvas.paste(img, (x, y), mask)
    return canvas.convert("RGB")


def crop_window(path, box):
    im = Image.open(path).convert("RGB")
    sx, sy = im.width / 1024, im.height / 640  # kutular 1024x640 küçük resme göre
    return im.crop((round(box[0] * sx), round(box[1] * sy), round(box[2] * sx), round(box[3] * sy)))


def terminal():
    """mindpkg terminal görünümü (Solarized koyu)"""
    tw, th = 640, 330
    im = Image.new("RGBA", (tw, th), (0, 43, 54, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, tw, 30], fill=(7, 54, 66, 255))
    for i, c in enumerate([(220, 50, 47), (181, 137, 0), (133, 153, 0)]):
        d.ellipse([12 + i * 20, 9, 24 + i * 20, 21], fill=c)
    ft = ImageFont.truetype(FONT, 14)
    d.text((tw // 2 - 40, 7), "Terminal", font=ft, fill=(147, 161, 161))
    f = ImageFont.truetype(MONO, 14)
    lines = [
        [((133, 153, 0), "user@mindos"), ((147, 161, 161), ":~$ "), ((238, 232, 213), "sudo mindpkg install chrome")],
        [((181, 137, 0), "MindOS Package Manager (mindpkg v1.3.0)")],
        [((133, 153, 0), "==> "), ((238, 232, 213), "Resmi üretici deposu ekleniyor: dl.google.com")],
        [((133, 153, 0), "==> "), ((238, 232, 213), "Sistem deposundan kuruluyor: google-chrome-stable")],
        [((133, 153, 0), "✓ Tamamlandı: "), ((238, 232, 213), "google-chrome-stable sisteme kuruldu.")],
        [],
        [((133, 153, 0), "user@mindos"), ((147, 161, 161), ":~$ "), ((238, 232, 213), "sudo mindpkg install vscode vlc gimp")],
        [((133, 153, 0), "✓ Tamamlandı: "), ((238, 232, 213), "code, vlc, gimp sisteme kuruldu.")],
        [],
        [((133, 153, 0), "user@mindos"), ((147, 161, 161), ":~$ "), ((238, 232, 213), "mindpkg search discord")],
        [((42, 161, 152), "  discord "), ((147, 161, 161), "1.0.156 [official]")],
        [((133, 153, 0), "user@mindos"), ((147, 161, 161), ":~$ "), ((38, 139, 210), "█")],
    ]
    y = 44
    for parts in lines:
        x = 16
        for color, text in parts:
            d.text((x, y), text, font=f, fill=color)
            x += d.textlength(text, font=f)
        y += 22
    return im


def stats():
    """Hafif & hızlı: dört bilgi kartı"""
    im = Image.new("RGBA", (660, 330), BG + (255,))
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(FONT, 40)
    big.set_variation_by_axes([800])
    small = ImageFont.truetype(FONT, 16)
    cards = [
        ("7.2", "Linux kernel · mindos", (38, 139, 210)),
        ("zram", "sıkıştırılmış bellek", (42, 161, 152)),
        ("−%28", "daha az RAM", (133, 153, 0)),
        ("1.5 GB", "kurulum kalıbı", (108, 113, 196)),
    ]
    for i, (num, label, color) in enumerate(cards):
        cx, cy = (i % 2) * 330 + 10, (i // 2) * 165 + 10
        d.rounded_rectangle([cx, cy, cx + 310, cy + 145], radius=18, fill=(238, 232, 213), outline=(211, 203, 183))
        d.rounded_rectangle([cx, cy, cx + 8, cy + 145], radius=4, fill=color)
        d.text((cx + 30, cy + 26), num, font=big, fill=color)
        d.text((cx + 32, cy + 90), label, font=small, fill=(88, 110, 117))
    return im


def save(img, name):
    img.save(os.path.join(OUT, name), optimize=True)
    print("✓", name)


welcome = Image.new("RGBA", (W, H), BG + (255,))
banner = Image.open(f"{B}/out/mindos-banner-dark.png").resize((540, 143), Image.LANCZOS)
welcome.alpha_composite(banner, ((W - 540) // 2, (H - 143) // 2))
save(welcome.convert("RGB"), "slide-welcome.png")
save(framed(terminal()), "slide-mindpkg.png")
save(framed(crop_window(f"{SHOTS}/arc-packages.ppm", (131, 44, 897, 624))), "slide-packages.png")
save(framed(crop_window(f"{SHOTS}/arc-maintenance.ppm", (131, 44, 897, 624))), "slide-maintenance.png")
save(framed(crop_window(f"{SHOTS}/mh-tr.ppm", (125, 30, 897, 636))), "slide-helper.png")
if os.path.exists(f"{SHOTS}/arcmenu.ppm"):
    save(framed(crop_window(f"{SHOTS}/arcmenu.ppm", (0, 0, 430, 493))), "slide-arcmenu.png")
speed = Image.new("RGBA", (W, H), BG + (255,))
speed.alpha_composite(stats(), ((W - 660) // 2, (H - 330) // 2))
save(speed.convert("RGB"), "slide-speed.png")
