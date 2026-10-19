#!/bin/bash
# MindOS uygulamalarını (Mind Arc, Mind Helper, MindOS dosyaları) tek bir .deb paketine toplar.
# Kaynak: imaj kök dizini (rootfs). Paket mindpkg'nin sistem bileşenleri kanalından dağıtılır,
# böylece Mind Arc/Mind Helper düzeltmeleri "mindpkg upgrade" ile kullanıcılara ulaşır.
# kullanım: build-mindos-apps.sh <rootfs> <sürüm> <çıktı_klasörü>     ör: ... rootfs 2026.10.14 release/
set -euo pipefail
R=$(readlink -f "$1"); VER=$2; OUT=$(readlink -f "$3")
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
P=$W/mindos-apps
FILES=(
  opt/mind-arc
  usr/bin/mind-arc usr/bin/mindhelper
  usr/share/mindhelper usr/share/mindos
  usr/share/applications/org.mindos.mind_arc.desktop usr/share/applications/mindhelper.desktop
  etc/xdg/autostart/mindhelper-autostart.desktop
  usr/share/gnome-shell/extensions/mindos-tweaks@mindos-official.github.io
  etc/dconf/db/local.d/20-mindos-shell
  usr/share/glib-2.0/schemas/91-mindos-extensions.gschema.override
  usr/share/glib-2.0/schemas/99_mindos-mutter.gschema.override
  usr/local/share/dbus-1/services/org.gnome.Shell.CalendarServer.service
  usr/lib/systemd/system/mindos-system-update.service
  usr/lib/systemd/system/system-update.target.wants/mindos-system-update.service
  usr/share/plymouth/themes/mindos/mindos.plymouth
  usr/share/plymouth/themes/mindos-update-tr
  usr/share/plymouth/themes/mindos-update-en
  usr/lib/os-release
  usr/libexec/mindos/mindos-avatar
  usr/lib/systemd/system/mindos-avatar.service
  usr/lib/systemd/system/multi-user.target.wants/mindos-avatar.service
  usr/lib/python3/dist-packages/mindos_prefs.py
  usr/libexec/mindos/mindos-update-notify
  usr/lib/systemd/user/mindos-update-notify.service
  usr/lib/systemd/user/mindos-update-notify.timer
  usr/lib/systemd/user/timers.target.wants/mindos-update-notify.timer
  usr/libexec/mindos/xkb-remove-variants
  etc/apt/apt.conf.d/80mindos-xkb
  usr/lib/systemd/system-sleep/mindos-touchpad
  etc/default/grub.d/10-mindos-osprober.cfg
  usr/libexec/mindos/fix-boot-order
  usr/lib/systemd/system/apt-daily.service.d/mindos-live.conf
  usr/lib/systemd/system/apt-daily-upgrade.service.d/mindos-live.conf
  etc/xdg/gnome-mimeapps.list
  etc/xdg/fastfetch/config.jsonc
  etc/xdg/fastfetch/logo-paradise.txt
)
mkdir -p "$P/DEBIAN"
for f in "${FILES[@]}"; do
    mkdir -p "$P/$(dirname "$f")"; cp -a "$R/$f" "$P/$f"
done
for i in "$R"/usr/share/icons/hicolor/*/apps/mind-arc.png "$R"/usr/share/icons/hicolor/*/apps/mindhelper.png "$R"/usr/share/icons/hicolor/scalable/apps/mindhelper.svg; do
    [ -e "$i" ] || continue
    rel=${i#"$R"/}; mkdir -p "$P/$(dirname "$rel")"; cp -a "$i" "$P/$rel"
done
find "$P" -name __pycache__ -prune -exec rm -rf {} +
find "$P" -name '*.pyc' -delete
SIZE=$(du -sk --exclude=DEBIAN "$P" | cut -f1)
cat > "$P/DEBIAN/control" <<CTL
Package: mindos-apps
Version: $VER
Architecture: all
Maintainer: MindOS Team <https://github.com/MindOS-Official>
Installed-Size: $SIZE
Depends: rfkill, nftables, unattended-upgrades, systemd-timesyncd, python3, python3-gi, python3-cairo, python3-psutil, python3-requests, gir1.2-gtk-3.0, gir1.2-gtk-4.0, gir1.2-adw-1, gir1.2-notify-0.7, pkexec
Section: misc
Priority: optional
Homepage: https://mindos-official.github.io/mindos_/
Description: MindOS Paradise applications and desktop defaults
 Mind Arc control center (system update, package center, maintenance,
 USB installer), Mind Helper assistant, MindOS Tweaks shell extension,
 restart-and-update service, boot splash settings, desktop defaults and
 shared MindOS files.
CTL
printf '%s\n' /etc/xdg/autostart/mindhelper-autostart.desktop /etc/dconf/db/local.d/20-mindos-shell \
    /etc/apt/apt.conf.d/80mindos-xkb /etc/default/grub.d/10-mindos-osprober.cfg \
    /etc/xdg/gnome-mimeapps.list /etc/xdg/fastfetch/config.jsonc /etc/xdg/fastfetch/logo-paradise.txt \
    > "$P/DEBIAN/conffiles"
# /usr/lib/os-release (MindOS Paradise kimliği) Debian'ın base-files paketine ait; bir Debian ara
# sürümü onu "Debian GNU/Linux" ile değiştirmesin diye base-files'ın kopyası kenara yönlendirilir.
cat > "$P/DEBIAN/preinst" <<'PR'
#!/bin/sh
set -e
if [ "$1" = install ] || [ "$1" = upgrade ]; then
    dpkg-divert --package mindos-apps --no-rename --divert /usr/lib/os-release.debian --add /usr/lib/os-release >/dev/null
    # fastfetch ayarı 1.0.2'ye kadar ISO'dan geliyordu (paketsiz). Kullanıcı değiştirmediyse kaldırılır ki
    # dpkg yenisini (mavi lotus logosu) kursun; değiştirdiyse dokunulmaz.
    f=/etc/xdg/fastfetch/config.jsonc
    if [ -f "$f" ] && [ "$(md5sum < "$f" | cut -d' ' -f1)" = 130635fd79ef6f8f0079045e9dfc5035 ]; then
        rm -f "$f"
    fi
fi
exit 0
PR
cat > "$P/DEBIAN/postrm" <<'PO'
#!/bin/sh
set -e
if [ "$1" = remove ] || [ "$1" = abort-install ] || [ "$1" = disappear ]; then
    dpkg-divert --package mindos-apps --rename --remove /usr/lib/os-release >/dev/null || true
fi
exit 0
PO
cat > "$P/DEBIAN/postinst" <<'PI'
#!/bin/sh
set -e
# MindOS varsayılan masaüstü ayarları (eklentiler, ArcMenu, menü görünümü) yeniden derlenir
if [ "$1" = configure ]; then
    command -v glib-compile-schemas >/dev/null && glib-compile-schemas /usr/share/glib-2.0/schemas || true
    command -v dconf >/dev/null && dconf update || true
    [ -d /run/systemd/system ] && systemctl daemon-reload || true
    /usr/libexec/mindos/mindos-avatar || true
    /usr/libexec/mindos/xkb-remove-variants || true
    # Otomatik güvenlik güncellemeleri varsayılan olarak açık (Mind Arc → Bakım'dan kapatıldıysa dosya
    # vardır ve dokunulmaz)
    if [ ! -e /etc/apt/apt.conf.d/20auto-upgrades ]; then
        printf 'APT::Periodic::Update-Package-Lists "1";\nAPT::Periodic::Unattended-Upgrade "1";\n' \
            > /etc/apt/apt.conf.d/20auto-upgrades
    fi
    # Bozuk bir önceki kurulumdan kalan UEFI kaydı MindOS'un önündeyse (grub rescue) MindOS başa alınır
    if [ -d /run/systemd/system ] && ! systemd-detect-virt --chroot --quiet && [ ! -e /run/live/medium ] && [ ! -e /var/lib/mindos/boot-order-checked ]; then
        mkdir -p /var/lib/mindos
        timeout 60 /usr/libexec/mindos/fix-boot-order >/dev/null 2>&1 || true
        : > /var/lib/mindos/boot-order-checked
    fi
    # Windows'un GRUB menüsünde görünmesi için (os-prober artık açık) menü bir kez yeniden üretilir
    if [ -f /boot/grub/grub.cfg ] && [ -d /run/systemd/system ] && ! systemd-detect-virt --chroot --quiet && [ ! -e /run/live/medium ] \
       && [ ! -e /var/lib/mindos/osprober-grub-updated-2 ]; then
        # -2: Türkçe dil ayarında os-prober Windows'u bulamıyordu (i/İ); düzeltmeyle menü bir kez daha üretilir
        mkdir -p /var/lib/mindos
        timeout 180 update-grub >/dev/null 2>&1 || true
        : > /var/lib/mindos/osprober-grub-updated-2
    fi
fi
exit 0
PI
chmod 755 "$P/DEBIAN/preinst" "$P/DEBIAN/postinst" "$P/DEBIAN/postrm"
( cd "$P" && find . -path ./DEBIAN -prune -o -type f -print | sed 's|^\./||' | sort | xargs -d '\n' md5sum > DEBIAN/md5sums )
dpkg-deb --root-owner-group -Zxz -b "$P" "$OUT/mindos-apps_${VER}_all.deb" >/dev/null
echo "$OUT/mindos-apps_${VER}_all.deb"
