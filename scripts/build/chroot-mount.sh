#!/usr/bin/env bash
# kullanım: chroot-mount.sh up|down <rootfs>
R="${2:-$(cd "$(dirname "$0")/.." && pwd)/rootfs}"
case "$1" in
  up)
    for d in dev dev/pts proc sys run; do mountpoint -q "$R/$d" || mount --bind "/$d" "$R/$d"; done
    [ -L "$R/etc/resolv.conf" ] && mv "$R/etc/resolv.conf" "$R/etc/resolv.conf.mindos-bak"
    cp -L /etc/resolv.conf "$R/etc/resolv.conf"
    printf '#!/bin/sh\nexit 101\n' > "$R/usr/sbin/policy-rc.d"; chmod +x "$R/usr/sbin/policy-rc.d"
    ;;
  down)
    rm -f "$R/usr/sbin/policy-rc.d"
    rm -f "$R/etc/resolv.conf"
    [ -e "$R/etc/resolv.conf.mindos-bak" ] || [ -L "$R/etc/resolv.conf.mindos-bak" ] && mv "$R/etc/resolv.conf.mindos-bak" "$R/etc/resolv.conf"
    for d in run sys proc dev/pts dev; do umount -l "$R/$d" 2>/dev/null; done
    ;;
esac
