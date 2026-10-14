#!/usr/bin/env bash
# chroot içinde: ISO paketlemeden önce son temizlik
export LANG=C
apt-get clean
rm -rf /var/lib/apt/lists/* /var/cache/apt/*.bin
mkdir -p /var/lib/apt/lists/partial
rm -f /var/lib/dpkg/*-old /var/cache/debconf/*-old
rm -rf /var/cache/man/* /var/cache/mindpkg/pkg/*
find /var/log -type f \( -name '*.gz' -o -name '*.[0-9]' -o -name '*.old' \) -delete
find /var/log -type f -exec truncate -s 0 {} +
rm -rf /tmp/* /var/tmp/* /root/.cache /root/.bash_history /root/.wget-hsts
: > /etc/machine-id
fc-cache -f >/dev/null 2>&1 || true
