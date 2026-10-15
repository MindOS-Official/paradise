#!/bin/bash
# Yeni bir Linux sürümünü MindOS kernel'i olarak hazırlar: indirir, kernel.org imzasıyla
# doğrular, MindOS ayarıyla derler (BTF açık, hata ayıklama paketi yok), kernel ve tüm
# modülleri MindOS Secure Boot anahtarıyla imzalar.
#
# kullanım: kernel/update-kernel.sh <sürüm> [paket_revizyonu]     ör: update-kernel.sh 7.3.1
# çıktı:    release/linux-image-<sürüm>-mindos_<sürüm>-<revizyon>_amd64.deb (imzalı)
#           release/linux-headers-<sürüm>-mindos_<sürüm>-<revizyon>_amd64.deb
# yayın:    pkgrepo/tools/publish_system.py <image.deb> <headers.deb>  (eski kernel kayıtlarını kaldırır)
#
# Derleme KBUILD klasöründe yapılır (BTF'li derleme ~20 GB yer ister; 16 GB'lık /dev/shm yetmez).
# Varsayılan: Samsung diskindeki ext4 imajı (MindOS_kbuild.img) /mnt/mindos-kbuild'e bağlanır.
# Uzun sürdüğü için systemd-run ile çalıştırın:
#   sudo systemd-run --unit=mindos-kernel --collect -p StandardOutput=file:/tmp/kernel.log \
#        -p StandardError=file:/tmp/kernel.log /bin/bash kernel/update-kernel.sh 7.3.1
set -euo pipefail
V=${1:?kullanım: $0 <sürüm> [revizyon]}
REV=${2:-1mindos}
P=$(cd "$(dirname "$0")" && pwd)
B=$(dirname "$P")
OUT=${OUT:-$B/release}
[[ $V =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?$ ]] || { echo "geçersiz sürüm: $V" >&2; exit 1; }
URL=https://cdn.kernel.org/pub/linux/kernel/v${V%%.*}.x
# Kernel.org checksum autosigner (https://www.kernel.org/signature.html)
AUTOSIGNER=B8868C80BA62A1FFFAF5FDA9632D3A06589DA6B1
TAR=$P/linux-$V.tar.xz
SUMS=$P/sha256sums-$V.asc
mkdir -p "$OUT"

# 1) İndir ve doğrula
export GNUPGHOME=$P/.gnupg-kernel
mkdir -p -m 700 "$GNUPGHOME"
gpg --batch --list-keys "$AUTOSIGNER" >/dev/null 2>&1 ||
    gpg --batch --auto-key-locate clear,wkd --locate-keys autosigner@kernel.org >/dev/null
[ -f "$TAR" ] || { curl -fL --proto =https -o "$TAR.part" "$URL/linux-$V.tar.xz" && mv "$TAR.part" "$TAR"; }
curl -fsSL --proto =https -o "$SUMS" "$URL/sha256sums.asc"
gpg --batch --status-fd 1 --verify "$SUMS" 2>/dev/null | grep -q "^\[GNUPG:\] VALIDSIG $AUTOSIGNER " ||
    { echo "HATA: sha256sums.asc kernel.org imzasıyla doğrulanamadı" >&2; exit 1; }
want=$(gpg --batch --decrypt "$SUMS" 2>/dev/null | awk -v f="linux-$V.tar.xz" '$2 == f {print $1}')
[ -n "$want" ] && [ "$(sha256sum "$TAR" | cut -d' ' -f1)" = "$want" ] ||
    { echo "HATA: linux-$V.tar.xz SHA256 imzalı listeyle uyuşmuyor" >&2; rm -f "$TAR"; exit 1; }
echo "✓ linux-$V.tar.xz kernel.org imzasıyla doğrulandı"

# 2) Derle (MindOS ayarı: config-mindos; yeni seçenekler varsayılan değerini alır)
KIMG=${KIMG:-/media/mamish/Samsung/MindOS_kbuild.img}
KBUILD=${KBUILD:-/mnt/mindos-kbuild}
if [ "$KBUILD" = /mnt/mindos-kbuild ] && ! mountpoint -q "$KBUILD"; then
    [ -f "$KIMG" ] || { truncate -s 40G "$KIMG"; mkfs.ext4 -q -L mindos-kbuild "$KIMG"; }
    mkdir -p "$KBUILD"; mount -o loop,noatime "$KIMG" "$KBUILD"
fi
W=$KBUILD/kbuild-$V
rm -rf "$W"; mkdir -p "$W"
echo "==> derleniyor: $W ($(date +%T))"
# başarıda derleme klasörü silinir; hata olursa inceleme için yerinde kalır
trap 'rc=$?; if [ $rc -eq 0 ]; then rm -rf "$W"; else echo "HATA (çıkış $rc): $BASH_COMMAND — klasör korundu: $W" >&2; fi' EXIT
tar -xf "$TAR" -C "$W"
cd "$W/linux-$V"
cp "$P/config-mindos" .config
./scripts/config --set-str LOCALVERSION "-mindos" --disable LOCALVERSION_AUTO \
    --enable DEBUG_INFO_BTF --enable DEBUG_INFO_BTF_MODULES --enable MODULE_ALLOW_BTF_MISMATCH
make olddefconfig >/dev/null
export DEB_BUILD_PROFILES="pkg.linux-upstream.nokerneldbg"   # -dbg paketi yok (~4 GB)
if ! make -j"$(nproc)" bindeb-pkg KDEB_PKGVERSION="$V-$REV" INSTALL_MOD_STRIP=1 >"$W/build.log" 2>&1; then
    tail -40 "$W/build.log" >&2
    exit 1
fi
cp .config "$P/config-$V-mindos"

echo "==> derlendi, imzalanıyor ($(date +%T))"
# 3) Secure Boot için imzala
DEB=$(ls "$W"/linux-image-"$V"-mindos_*_amd64.deb | grep -v -- -dbg_)
"$B/secureboot/sign-kernel-deb.sh" "$DEB" "$V-$REV" "$OUT"
# Kernel başlıkları (DKMS: NVIDIA, VirtualBox ...); imza gerekmez, isteğe bağlı bileşen olarak yayınlanır
cp "$W"/linux-headers-"$V"-mindos_"$V-$REV"_amd64.deb "$OUT/"
cp "$P/config-$V-mindos" "$P/config-mindos"   # sonraki sürüm bu ayardan başlar
echo "✓ hazır: $OUT/linux-image-$V-mindos_$V-${REV}_amd64.deb"
