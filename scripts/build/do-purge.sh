#!/usr/bin/env bash
# chroot içinde çalışır: dil/şişkinlik paketlerini kaldırır (sadece /tmp/purge.txt listesindekiler + açıkta kalanlar)
set -e
export LANG=C DEBIAN_FRONTEND=noninteractive
# Korunacaklar: Türkçe dil desteği + MindOS uygulamalarının bağımlılıkları
apt-mark manual task-turkish task-turkish-desktop firefox-esr-l10n-tr libreoffice-l10n-tr manpages-tr \
  gnome-themes-extra python3-psutil python3-requests python3-setproctitle python3-gi python3-gi-cairo python3-cairo \
  gir1.2-notify-0.7 gir1.2-adw-1 gir1.2-gtk-3.0 gir1.2-gtk-4.0 gir1.2-ibus-1.0 $(dpkg-query -Wf '${Package}\n' 'thunderbird-l10n-tr' 2>/dev/null) >/dev/null
apt-get purge -y --autoremove $(cat /tmp/purge.txt)
apt-get autoremove --purge -y
apt-get clean
