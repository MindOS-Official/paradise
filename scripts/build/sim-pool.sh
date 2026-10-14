#!/usr/bin/env bash
# chroot içinde: sadece ISO deposu (/mnt/media) ile Calamares'in kuracağı paketleri SİMÜLE eder
export LANG=C
mkdir -p /tmp/aptsim/lists/partial /tmp/aptsim/cache/archives/partial
echo "deb [trusted=yes] file:/mnt/media trixie main non-free-firmware" > /tmp/aptsim/sources.list
O="-o Dir::Etc::sourcelist=/tmp/aptsim/sources.list -o Dir::Etc::sourceparts=- -o Dir::State::lists=/tmp/aptsim/lists -o Dir::Cache=/tmp/aptsim/cache -o APT::Get::List-Cleanup=0"
apt-get $O update >/dev/null 2>&1
for set in "grub-efi" "grub-pc" "cryptsetup-initramfs cryptsetup keyutils"; do
  apt-get $O -s install $set 2>&1 | awk '/^Inst /{print $2}'
  apt-get $O -s install $set 2>&1 | grep -E "^E:" >&2
done | sort -u
