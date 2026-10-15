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

echo "[2/4] filesystem.squashfs (xz + x86 BCJ, 1M blok)..."
rm -f "$I/live/filesystem.squashfs"
mksquashfs "$R" "$I/live/filesystem.squashfs" \
    -noappend -comp xz -b 1M -Xbcj x86 -Xdict-size 100% \
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

echo "[✓] $OUT ($(du -h "$OUT" | cut -f1))"
