#!/bin/bash
# MindOS Paradise derleme klasöründen (paradise-build) bu repoyu günceller.
# Programların kaynakları src/, sistem dosyaları overlay/ (overlay.list), ISO önyükleme
# ayarları iso/, kernel ve Secure Boot betikleri ayrı klasörlere kopyalanır.
# Gizli anahtarlar asla kopyalanmaz; sonda ayrıca taranır, bulunursa betik hata verir.
# kullanım: scripts/export-from-build.sh /yol/paradise-build
set -euo pipefail
B=$(readlink -f "${1:?kullanım: $0 <paradise-build klasörü>}")
REPO=$(cd "$(dirname "$0")/.." && pwd)
R=$B/rootfs
[ -d "$R/usr" ] || { echo "imaj kökü bulunamadı: $R" >&2; exit 1; }
cd "$REPO"

rm -rf src overlay iso kernel secureboot branding tests third_party packages scripts/build
mkdir -p src overlay iso kernel secureboot branding tests/vm third_party packages

copy() {  # copy <kaynak> <hedef_klasör> [rsync seçenekleri...]
    local s=$1 d=$2; shift 2
    rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='*.orig' --exclude='*.bak' "$@" "$s" "$d"
}

# --- Programlar
mkdir -p src/mindpkg src/mind-arc
copy "$B/mindpkg/mindpkg" src/mindpkg/
copy "$B/mind-arc/" src/mind-arc/ --exclude='usb-writer.live-version'
copy "$R/opt/mind-arc/icon.png" src/mind-arc/
copy "$R/usr/share/mindhelper/" src/mindhelper/
copy "$B/branding/mindos-tweaks@mindos-official.github.io" src/shell-extension/

# --- Paketlenmiş üçüncü taraf GNOME eklentisi (GPL-3, Debian'da bu sürümü yok)
copy "$R/usr/share/gnome-shell/extensions/blur-my-shell@aunetx" third_party/

# --- Sistem dosyaları (overlay.list)
missing=0
while read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    found=0
    for p in $R/$line; do
        [ -e "$p" ] || [ -L "$p" ] || continue
        found=1
        rel=${p#"$R"/}
        mkdir -p "overlay/$(dirname "$rel")"
        rsync -a --exclude='__pycache__' "$p" "overlay/$(dirname "$rel")/"
    done
    [ $found = 1 ] || { echo "UYARI: imajda yok: $line" >&2; missing=1; }
done < overlay.list

# --- ISO önyükleme ayarları
for f in boot/grub/grub.cfg boot/grub/config.cfg boot/grub/loopback.cfg boot/grub/theme.cfg \
         boot/grub/live-theme/theme.txt isolinux/isolinux.cfg isolinux/menu.cfg isolinux/stdmenu.cfg \
         isolinux/live.cfg isolinux/utilities.cfg; do
    mkdir -p "iso/$(dirname "$f")"; cp -a "$B/iso_root/$f" "iso/$f"
done

# --- Kernel, Secure Boot (yalnızca betikler ve herkese açık sertifikalar)
copy "$B/kernel/build-btf.sh" kernel/
copy "$B/kernel/update-kernel.sh" kernel/
copy "$B/kernel/LOCKDOWN-TODO.md" kernel/
copy "$B/kernel/config-mindos" kernel/
copy "$B/kernel/config-7.2.10-mindos" kernel/
cp "$R/boot/config-7.2.10-mindos" kernel/config-7.2.10-mindos.shipped  # ISO'daki kernel'in birebir ayarı
copy "$B/kernel/sha256sums.asc" kernel/
copy "$B/scripts/kernel-config-mindos.sh" kernel/
for f in sign-kernel.sh sign-kernel-deb.sh MOK.crt MindOS-SecureBoot.der mindpkg-release.pub efi-grub.cfg; do
    copy "$B/secureboot/$f" secureboot/
done

# --- Markalama betikleri, derleme betikleri, sanal makine testleri, paket listesi
copy "$B/branding/" branding/ --exclude='mindos-tweaks@*' --exclude='out'
copy "$B/scripts/" scripts/build/ --exclude='kernel-config-mindos.sh'
for f in "$B"/vmtest/*.sh "$B"/vmtest/*.py; do copy "$f" tests/vm/; done
cp "$B/iso_root/live/filesystem.manifest" packages/filesystem.manifest

# --- Güvenlik kapısı: özel anahtar ya da gizli dosya repoya asla girmez
leak=$( { grep -rIlE --exclude-dir=.git -e '-----BEGIN ([A-Z]+ )?PRIVATE KEY-----' . || true
          find . -path ./.git -prune -o \( -name '*.key' -o -name 'MOK.priv' -o -name '*.p12' -o -name 'id_rsa*' \) -print; } )
if [ -n "$leak" ]; then
    echo "HATA: gizli anahtar bulundu, repo kullanılmamalı:" >&2; echo "$leak" >&2; exit 2
fi
echo "Tamam: $(find src overlay iso kernel secureboot branding scripts tests third_party packages -type f | wc -l) dosya"
exit $missing
