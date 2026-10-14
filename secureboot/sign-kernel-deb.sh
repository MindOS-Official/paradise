#!/bin/bash
# Kernel .deb paketini Secure Boot için imzalı olarak yeniden paketler (vmlinuz + tüm modüller).
# kullanım: sign-kernel-deb.sh <girdi.deb> <yeni_sürüm> <çıktı_klasörü>
#   ör: sign-kernel-deb.sh linux-image-7.2.10-mindos_7.2.10-2mindos_amd64.deb 7.2.10-3mindos out/
set -euo pipefail
K=$(dirname "$(readlink -f "$0")")
IN=$(readlink -f "$1"); VER=$2; OUT=$(readlink -f "$3")
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
dpkg-deb -R "$IN" "$W/pkg"
KV=$(ls "$W/pkg/lib/modules" 2>/dev/null || ls "$W/pkg/usr/lib/modules" 2>/dev/null || true)
VM=$(ls "$W"/pkg/boot/vmlinuz-*)
sbsign --key "$K/MOK.key" --cert "$K/MOK.crt" --output "$VM.s" "$VM" >/dev/null && mv "$VM.s" "$VM"
sbverify --cert "$K/MOK.crt" "$VM" >/dev/null
M=$(ls -d "$W"/pkg/lib/modules/"$KV" "$W"/pkg/usr/lib/modules/"$KV" 2>/dev/null | head -1 || true)
[ -d "$M" ] || { echo "modül dizini yok"; exit 1; }
sign_one() { f=$1; t=${f%.zst}; zstd -q -d -f "$f" -o "$t"; kmodsign sha256 "$KEY" "$CRT" "$t"; zstd -q -19 -f --rm "$t" -o "$f"; }
export -f sign_one; export KEY="$K/MOK.key" CRT="$K/MindOS-SecureBoot.der"
find "$M" -name '*.ko.zst' -print0 | xargs -0 -n 1 -P "$(nproc)" bash -c 'sign_one "$0"'
find "$M" -name '*.ko' -print0 | xargs -0 -r -n 1 kmodsign sha256 "$KEY" "$CRT"
sed -i -E "s/^Version: .*/Version: $VER/" "$W/pkg/DEBIAN/control"
# md5sums imzalı dosyalarla güncellenir (dpkg --verify temiz kalsın)
( cd "$W/pkg" && find . -path ./DEBIAN -prune -o -type f -print | sed 's|^\./||' | sort | xargs -d '\n' md5sum > DEBIAN/md5sums )
NAME=$(sed -n 's/^Package: //p' "$W/pkg/DEBIAN/control")
dpkg-deb --root-owner-group -Zzstd -b "$W/pkg" "$OUT/${NAME}_${VER}_amd64.deb" >/dev/null
echo "$OUT/${NAME}_${VER}_amd64.deb"
