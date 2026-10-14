#!/usr/bin/env python3
"""Kurulu sistemin GRUB arka planı: lotus deseninin koyu sürümü.

GRUB_BACKGROUND kullanıldığında Debian'ın betiği menü renklerini ayarlamaz ve
menü açık gri yazıyla çizilir; yazıların okunması için arka plan koyu olmalı.
kullanım: make-grub-bg.py <duvar_kağıdı.jpg> <çıktı.jpg>
"""
import sys

from PIL import Image, ImageEnhance

src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB").resize((1920, 1080), Image.LANCZOS)
im = ImageEnhance.Color(im).enhance(0.8)
navy = Image.new("RGB", im.size, (6, 22, 36))
dark = Image.blend(navy, im, 0.22)  # desen hafifçe seçilir, yazı net okunur
dark.save(out, quality=92, optimize=True)  # baseline JPEG (GRUB progressive okuyamaz)
print(out, dark.size)
