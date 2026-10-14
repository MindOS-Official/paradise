#!/usr/bin/env bash
# chroot içinde çalışır: MindOS Paradise RAM / açılış optimizasyonu
set -e
export LANG=C DEBIAN_FRONTEND=noninteractive

# 1) zram swap (RAM'in yarısı, en fazla 8GB, zstd). zram varken zswap gereksiz -> kapat
apt-get install -y --no-install-recommends systemd-zram-generator
cat > /etc/systemd/zram-generator.conf <<'Z'
[zram0]
zram-size = min(ram / 2, 8192)
compression-algorithm = zstd
swap-priority = 100
Z
cat > /etc/tmpfiles.d/mindos-zswap-off.conf <<'Z'
# MindOS: zram swap kullanıldığı için zswap kapalı (çift sıkıştırmayı önler)
w- /sys/module/zswap/parameters/enabled - - - - N
Z

# 2) Bellek yönetimi sysctl ayarları (zram için önerilen değerler)
cat > /etc/sysctl.d/90-mindos-memory.conf <<'Z'
# MindOS Paradise bellek ayarları
vm.swappiness = 180
vm.page-cluster = 0
vm.watermark_boost_factor = 0
vm.watermark_scale_factor = 125
vm.vfs_cache_pressure = 50
vm.dirty_bytes = 268435456
vm.dirty_background_bytes = 67108864
Z

# 3) journald: bellek ve disk sınırı
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/90-mindos.conf <<'Z'
[Journal]
SystemMaxUse=64M
RuntimeMaxUse=32M
Compress=yes
Z

# 4) Açılışta gereksiz servisler (paketler kurulu kalır, gerektiğinde açılabilir)
for u in ModemManager.service cups-browsed.service cups.service sysstat.service smartmontools.service \
         NetworkManager-wait-online.service lvm2-monitor.service \
         sysstat-collect.timer sysstat-summary.timer sysstat-rotate.timer fwupd-refresh.timer man-db.timer \
         mdcheck_continue.timer mdcheck_start.timer mdmonitor-oneshot.timer xfs_scrub_all.timer system-xfs_scrub.slice; do
  systemctl disable "$u" 2>/dev/null || true
done
# CUPS sadece yazdırma istendiğinde (socket/path aktivasyonu) başlasın
systemctl enable cups.socket cups.path 2>/dev/null || true

# 5) Kaldırılmış paketlerden kalan ölü autostart / user servisleri
rm -f /etc/xdg/autostart/localsearch-3.desktop
find /etc/systemd/user -xtype l -delete
find /etc/systemd/system -xtype l -delete

# 6) Evolution alarm bildirimi (evolution kaldırıldı, ~40MB RAM)
if [ -f /etc/xdg/autostart/org.gnome.Evolution-alarm-notify.desktop ]; then
  grep -q '^Hidden=true' /etc/xdg/autostart/org.gnome.Evolution-alarm-notify.desktop || \
    echo 'Hidden=true' >> /etc/xdg/autostart/org.gnome.Evolution-alarm-notify.desktop
fi

# 7) Dosya indeksleyici (localsearch/tracker) - nautilus bağımlı olduğu için kaldırılamaz, maskelenir
rm -f /etc/systemd/user/gnome-session.target.wants/localsearch-3.service
for u in localsearch-3.service localsearch-control-3.service localsearch-writeback-3.service; do
  ln -sf /dev/null /etc/systemd/user/$u
done
cat > /usr/share/glib-2.0/schemas/92-mindos-performance.gschema.override <<'Z'
[org.freedesktop.Tracker3.Miner.Files]
crawling-interval=-2
enable-monitors=false
index-recursive-directories=[]
index-single-directories=[]
Z
glib-compile-schemas /usr/share/glib-2.0/schemas
