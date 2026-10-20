#!/usr/bin/env bash
# MindOS Paradise: rootfs + iso_root -> hibrit (BIOS + UEFI) ISO
# kullanım: sudo build-iso.sh <build_dizini> <cikti.iso>
set -euo pipefail
B="${1:?build dizini (rootfs/ ve iso_root/ içeren)}"
# Kaynaktaki programlar imajdakiyle aynı olmalı (eski bir kopya ISO'ya girmesin)
for pair in "mindpkg/mindpkg:usr/local/bin/mindpkg" "mind-arc/main.py:opt/mind-arc/main.py" \
            "mind-arc/mindarc_extra.py:opt/mind-arc/mindarc_extra.py"; do
    src=$B/${pair%%:*}; dst=$B/rootfs/${pair#*:}
    if [ -f "$src" ] && ! cmp -s "$src" "$dst"; then
        echo "HATA: $dst kaynaktaki $src ile aynı değil; önce imaja kurun." >&2; exit 1
    fi
done
OUT="${2:?çıktı ISO yolu}"
R="$B/rootfs"
I="$B/iso_root"

VOLID="MindOS Paradise"

for d in dev/pts dev proc sys run; do
    if mountpoint -q "$R/$d"; then echo "[HATA] $R/$d hâlâ bağlı, önce chroot-mount.sh down"; exit 1; fi
done

echo "[1/4] Manifest ve boyut bilgisi..."
chroot "$R" dpkg-query -W --showformat='${Package}\t${Version}\n' > "$I/live/filesystem.manifest"
du -sx --block-size=1 "$R" | cut -f1 > "$I/live/filesystem.size"

TARGET_ARCH=${3:-${ARCH:-$(chroot "$R" dpkg --print-architecture 2>/dev/null || uname -m)}}
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
P=$(cd "$SCRIPT_DIR/../.." && pwd)

if [ "$TARGET_ARCH" = "arm64" ] || [ "$TARGET_ARCH" = "aarch64" ]; then
    BCJ_OPT=""
    IS_ARM=true
    echo "[*] Mimari: arm64 / aarch64 (UEFI önyükleme)"
    # ARM64 efi.img ve EFI/boot ağacını hazırla
    "$SCRIPT_DIR/create-efi-img.sh" "$I/boot/grub/efi.img" "$TARGET_ARCH" "$R"
    mkdir -p "$I/EFI/boot"
    if [ -f "$P/secureboot/arm64-efi/bootaa64.efi" ]; then
        cp -f "$P/secureboot/arm64-efi/bootaa64.efi" "$I/EFI/boot/bootaa64.efi"
        cp -f "$P/secureboot/arm64-efi/grubaa64.efi" "$I/EFI/boot/grubaa64.efi" 2>/dev/null || true
        cp -f "$P/secureboot/arm64-efi/mmaa64.efi" "$I/EFI/boot/mmaa64.efi" 2>/dev/null || true
    fi
else
    BCJ_OPT="-Xbcj x86"
    IS_ARM=false
    echo "[*] Mimari: x86_64 / amd64 (BCJ: x86, BIOS + UEFI hibrit önyükleme)"
    if [ ! -f "$I/boot/grub/efi.img" ]; then
        "$SCRIPT_DIR/create-efi-img.sh" "$I/boot/grub/efi.img" "$TARGET_ARCH" "$R"
    fi
fi

echo "[2/4] filesystem.squashfs (xz + $BCJ_OPT, 1M blok)..."
rm -f "$I/live/filesystem.squashfs"
mksquashfs "$R" "$I/live/filesystem.squashfs" \
    -noappend -comp xz -b 1M $BCJ_OPT -Xdict-size 100% \
    -wildcards -e 'proc/*' 'sys/*' 'dev/*' 'run/*' 'tmp/*' 'var/tmp/*' 'mnt/*' \
    -progress -mem 4G

echo "[3/4] Disk bilgisi ve sağlama toplamları..."
echo "MindOS Paradise" > "$I/.disk/info"
(
    cd "$I"
    find . -type f ! -name md5sum.txt ! -name sha256sum.txt ! -path './isolinux/boot.cat' ! -path './isolinux/isolinux.bin' -print0 \
        | sort -z | xargs -0 md5sum > md5sum.txt
    find . -type f ! -name md5sum.txt ! -name sha256sum.txt ! -path './isolinux/boot.cat' ! -path './isolinux/isolinux.bin' -print0 \
        | sort -z | xargs -0 sha256sum > sha256sum.txt
)

echo "[4/4] ISO üretiliyor..."
rm -f "$OUT"
if [ "$IS_ARM" = true ]; then
    xorriso -as mkisofs \
        -r -J -joliet-long -iso-level 3 \
        -V "$VOLID" \
        -partition_offset 16 \
        -e boot/grub/efi.img -no-emul-boot \
        -isohybrid-gpt-basdat \
        -o "$OUT" "$I"
else
    xorriso -as mkisofs \
        -r -J -joliet-long -iso-level 3 \
        -V "$VOLID" \
        -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
        -partition_offset 16 \
        -c isolinux/boot.cat \
        -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
        -eltorito-alt-boot \
        -e boot/grub/efi.img -no-emul-boot \
        -isohybrid-gpt-basdat -isohybrid-apm-hfsplus \
        -o "$OUT" "$I"
fi

echo "[✓] $OUT ($(du -h "$OUT" | cut -f1))"
