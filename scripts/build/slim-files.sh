#!/usr/bin/env bash
# chroot içinde: doküman/çeviri budama (TR + EN korunur) ve kalıcı dpkg kuralları
set -e
cat > /etc/dpkg/dpkg.cfg.d/01-mindos-slim <<'D'
# MindOS Paradise: sadece Türkçe + İngilizce çeviri/kılavuz, lisans dosyaları korunur
path-exclude=/usr/share/doc/*
path-include=/usr/share/doc/*/copyright
path-exclude=/usr/share/man/*
path-include=/usr/share/man/man[1-9]*
path-include=/usr/share/man/tr*
path-exclude=/usr/share/locale/*
path-include=/usr/share/locale/locale.alias
path-include=/usr/share/locale/tr/*
path-include=/usr/share/locale/en/*
path-include=/usr/share/locale/en_US/*
path-exclude=/usr/share/help/*
path-include=/usr/share/help/C/*
path-include=/usr/share/help/tr/*
path-exclude=/usr/share/info/*
path-exclude=/usr/share/gnome/help/*
path-exclude=/usr/share/omf/*
path-exclude=/usr/share/lintian/*
path-exclude=/usr/share/linda/*
D

# Mevcut dosyalara aynı kuralları uygula
find /usr/share/doc -mindepth 1 ! -type d ! -name copyright -delete
find /usr/share/doc -mindepth 1 -type d -empty -delete
find /usr/share/man -mindepth 1 -maxdepth 1 -type d ! -name 'man[1-9]*' ! -name 'tr*' -exec rm -rf {} +
find /usr/share/locale -mindepth 1 -maxdepth 1 ! -name locale.alias ! -name tr ! -name en ! -name en_US -exec rm -rf {} +
find /usr/share/help -mindepth 1 -maxdepth 1 ! -name C ! -name tr -exec rm -rf {} + 2>/dev/null || true
rm -rf /usr/share/info/* /usr/share/gnome/help/* /usr/share/omf/* /usr/share/lintian/* /usr/share/linda/*

# Locale: locales-all kaldırıldı -> sadece TR ve EN üret
sed -i -E 's/^# *(tr_TR.UTF-8 UTF-8)/\1/; s/^# *(en_US.UTF-8 UTF-8)/\1/' /etc/locale.gen
locale-gen >/dev/null

# Python bayt kodu önbellekleri (çalışma anında yeniden üretilir)
find / -xdev \( -path /proc -o -path /sys -o -path /dev -o -path /run \) -prune -o -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
