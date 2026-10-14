#!/bin/bash
# MindOS kernel'ini ve tüm modüllerini MindOS Secure Boot anahtarıyla imzalar.
# Secure Boot açıkken kernel imzasız modülleri reddeder (IMA arch policy), bu yüzden ikisi de gerekir.
# kullanım: sudo sign-kernel.sh <rootfs> <kernel_sürümü>     ör: sign-kernel.sh /path/rootfs 7.2.10-mindos
set -euo pipefail
K=$(dirname "$(readlink -f "$0")")
R=$1; KV=$2
KEY=$K/MOK.key; CRT=$K/MindOS-SecureBoot.der
M=$R/lib/modules/$KV
[ -d "$M" ] || { echo "modül dizini yok: $M"; exit 1; }

# 1) Kernel imajı (zaten imzalıysa yeniden imzalamaz)
VM=$R/boot/vmlinuz-$KV
if ! sbverify --cert $K/MOK.crt "$VM" >/dev/null 2>&1; then
    sbsign --key "$KEY" --cert $K/MOK.crt --output "$VM.signed" "$VM" && mv "$VM.signed" "$VM"
fi
sbverify --cert $K/MOK.crt "$VM" >/dev/null && echo "✓ kernel imzalı: $VM"

# 2) Modüller: aç -> imzala -> tekrar sıkıştır
sign_one() {
    f=$1
    tmp=${f%.zst}
    zstd -q -d -f "$f" -o "$tmp"
    kmodsign sha256 "$KEY" "$CRT" "$tmp"
    zstd -q -19 -f --rm "$tmp" -o "$f"
}
export -f sign_one; export KEY CRT
find "$M" -name '*.ko.zst' -print0 | xargs -0 -n 1 -P "$(nproc)" bash -c 'sign_one "$0"'
find "$M" -name '*.ko' -print0 | xargs -0 -r -n 1 kmodsign sha256 "$KEY" "$CRT"
echo "✓ $(find "$M" -name '*.ko*' | wc -l) modül imzalandı"
