#!/usr/bin/env bash
# MindOS Paradise: UEFI efi.img üretici betiği (arm64, x86_64 veya hibrit çoklu mimari)
# kullanım: create-efi-img.sh <hedef_efi.img> [arm64|x86_64|both] [kaynak_rootfs]
set -euo pipefail

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

OUT="${1:?çıktı efi.img yolu gerekli}"
ARCH="${2:-$(uname -m)}"
R="${3:-}"

P=$(cd "$(dirname "$0")/../.." && pwd)
SECUREBOOT_DIR="$P/secureboot"
CER="$SECUREBOOT_DIR/MindOS-SecureBoot.der"

case "$ARCH" in
    arm64|aarch64) MODE="arm64" ;;
    x86_64|amd64)  MODE="x86_64" ;;
    both|multi)    MODE="both" ;;
    *)             MODE="x86_64" ;;
esac

echo "[*] efi.img hazırlanıyor: $OUT (Mimari: $MODE)..."
mkdir -p "$(dirname "$OUT")"

# 16 MB FAT imajı oluştur (hem x86_64 hem arm64 ikilileri rahatça sığsın)
IMG_SIZE_MB=16
truncate -s "${IMG_SIZE_MB}M" "$OUT"
mkfs.vfat -F 12 -n "MINDOS_EFI" "$OUT" >/dev/null

W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT

mkdir -p "$W/EFI/boot" "$W/EFI/mindos" "$W/boot/grub"

# 1) GRUB önyükleyici yapılandırması
cat > "$W/boot/grub/grub.cfg" <<'EOF'
search --set=root --file /.disk/info
set prefix=($root)/boot/grub
configfile ($root)/boot/grub/grub.cfg
EOF
cp "$W/boot/grub/grub.cfg" "$W/EFI/boot/grub.cfg"

# 2) Secure Boot sertifikası
if [ -f "$CER" ]; then
    cp "$CER" "$W/EFI/mindos/MindOS-SecureBoot.cer"
elif [ -n "$R" ] && [ -f "$R/usr/share/mindos/secureboot/MindOS-SecureBoot.der" ]; then
    cp "$R/usr/share/mindos/secureboot/MindOS-SecureBoot.der" "$W/EFI/mindos/MindOS-SecureBoot.cer"
fi

# 3) EFI ikililerini kopyala
copy_x86() {
    if [ -n "$R" ] && [ -f "$R/usr/lib/shim/shimx64.efi.signed" ]; then
        cp "$R/usr/lib/shim/shimx64.efi.signed" "$W/EFI/boot/bootx64.efi"
        cp "$R/usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed" "$W/EFI/boot/grubx64.efi" 2>/dev/null || true
        cp "$R/usr/lib/shim/mmx64.efi" "$W/EFI/boot/mmx64.efi" 2>/dev/null || true
    elif [ -f /usr/lib/shim/shimx64.efi.signed ]; then
        cp /usr/lib/shim/shimx64.efi.signed "$W/EFI/boot/bootx64.efi"
        cp /usr/lib/grub/x86_64-efi-signed/grubx64.efi.signed "$W/EFI/boot/grubx64.efi" 2>/dev/null || true
        cp /usr/lib/shim/mmx64.efi "$W/EFI/boot/mmx64.efi" 2>/dev/null || true
    elif [ -f "$SECUREBOOT_DIR/bootx64.efi" ]; then
        cp "$SECUREBOOT_DIR/bootx64.efi" "$W/EFI/boot/bootx64.efi"
        cp "$SECUREBOOT_DIR/grubx64.efi" "$W/EFI/boot/grubx64.efi" 2>/dev/null || true
        cp "$SECUREBOOT_DIR/mmx64.efi" "$W/EFI/boot/mmx64.efi" 2>/dev/null || true
    fi
}

copy_arm64() {
    if [ -n "$R" ] && [ -f "$R/usr/lib/shim/shimaa64.efi.signed" ]; then
        cp "$R/usr/lib/shim/shimaa64.efi.signed" "$W/EFI/boot/bootaa64.efi"
        cp "$R/usr/lib/grub/arm64-efi-signed/grubaa64.efi.signed" "$W/EFI/boot/grubaa64.efi" 2>/dev/null || true
        cp "$R/usr/lib/shim/mmaa64.efi" "$W/EFI/boot/mmaa64.efi" 2>/dev/null || true
    elif [ -f "$SECUREBOOT_DIR/arm64-efi/bootaa64.efi" ]; then
        cp "$SECUREBOOT_DIR/arm64-efi/bootaa64.efi" "$W/EFI/boot/bootaa64.efi"
        cp "$SECUREBOOT_DIR/arm64-efi/grubaa64.efi" "$W/EFI/boot/grubaa64.efi" 2>/dev/null || true
        cp "$SECUREBOOT_DIR/arm64-efi/mmaa64.efi" "$W/EFI/boot/mmaa64.efi" 2>/dev/null || true
    elif [ -f "$SECUREBOOT_DIR/bootaa64.efi" ]; then
        cp "$SECUREBOOT_DIR/bootaa64.efi" "$W/EFI/boot/bootaa64.efi"
        cp "$SECUREBOOT_DIR/grubaa64.efi" "$W/EFI/boot/grubaa64.efi" 2>/dev/null || true
        cp "$SECUREBOOT_DIR/mmaa64.efi" "$W/EFI/boot/mmaa64.efi" 2>/dev/null || true
    fi
}

case "$MODE" in
    x86_64) copy_x86 ;;
    arm64)  copy_arm64 ;;
    both)   copy_x86; copy_arm64 ;;
esac

# Önyükleyici doğrulaması
if [ ! -f "$W/EFI/boot/bootx64.efi" ] && [ ! -f "$W/EFI/boot/bootaa64.efi" ]; then
    echo "[HATA] Hiçbir EFI önyükleyici ikilisi bulunamadı ($MODE)!" >&2
    exit 1
fi

# 4) Dosyaları FAT imajına aktar (mcopy ile losetup / root gerektirmeden çalışır)
if command -v mcopy >/dev/null 2>&1; then
    mcopy -s -i "$OUT" "$W/EFI" "::"
    mcopy -s -i "$OUT" "$W/boot" "::"
else
    # mcopy yoksa loop mount kullan (root yetkisi ile)
    MNT=$(mktemp -d)
    mount -o loop "$OUT" "$MNT"
    cp -r "$W"/* "$MNT"/
    umount "$MNT"
    rmdir "$MNT"
fi

echo "[✓] efi.img başarıyla oluşturuldu: $OUT"
