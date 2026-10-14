#!/bin/bash
# Bu repoyu bir Debian 13 (GNOME) imaj köküne uygular: MindOS programları + sistem dosyaları.
# Ardından scripts/build/build-mindos-apps.sh ile mindos-apps paketi üretilip köke kurulur.
# kullanım: sudo scripts/apply-overlay.sh <imaj_kökü>
set -euo pipefail
REPO=$(cd "$(dirname "$0")/.." && pwd)
R=$(readlink -f "${1:?kullanım: $0 <imaj_kökü>}")
[ "$(id -u)" = 0 ] || { echo "root yetkisi gerekli" >&2; exit 1; }
[ -d "$R/usr" ] || { echo "imaj kökü değil: $R" >&2; exit 1; }

cp -a "$REPO/overlay/." "$R/"
install -D -m 755 "$REPO/src/mindpkg/mindpkg" "$R/usr/local/bin/mindpkg"
mkdir -p "$R/opt/mind-arc" "$R/usr/share/mindhelper"
rsync -a --delete "$REPO/src/mind-arc/" "$R/opt/mind-arc/"
rsync -a --delete "$REPO/src/mindhelper/" "$R/usr/share/mindhelper/"
E=$R/usr/share/gnome-shell/extensions
for ext in "$REPO"/src/shell-extension/*@* "$REPO"/third_party/*@*; do
    mkdir -p "$E/$(basename "$ext")"
    rsync -a --delete "$ext/" "$E/$(basename "$ext")/"
done
cp "$REPO"/third_party/blur-my-shell@aunetx/schemas/*.gschema.xml "$R/usr/share/glib-2.0/schemas/"
chroot "$R" sh -c 'glib-compile-schemas /usr/share/glib-2.0/schemas && dconf update'
echo "Uygulandı: $R"
