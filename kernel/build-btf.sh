#!/bin/bash
# 7.2.10-mindos'u BTF ile yeniden derler (systemd BPF özellikleri için /sys/kernel/btf/vmlinux gerekir)
set -euo pipefail
P=$(cd "$(dirname "$0")" && pwd)
B=/dev/shm/kbuild
rm -rf $B; mkdir -p $B; cd $B
tar -xf $P/linux-7.2.10.tar.xz
cd linux-7.2.10
cp $P/config-7.2.10-mindos .config
./scripts/config --disable DEBUG_INFO_NONE --enable DEBUG_INFO --enable DEBUG_INFO_DWARF5 \
  --disable DEBUG_INFO_REDUCED --disable DEBUG_INFO_SPLIT \
  --enable DEBUG_INFO_COMPRESSED_ZLIB --disable DEBUG_INFO_COMPRESSED_NONE \
  --enable DEBUG_INFO_BTF --enable DEBUG_INFO_BTF_MODULES --enable MODULE_ALLOW_BTF_MISMATCH \
  --set-str LOCALVERSION "-mindos" --disable LOCALVERSION_AUTO
make olddefconfig >/dev/null
grep -E "^CONFIG_DEBUG_INFO_BTF|^CONFIG_DEBUG_INFO_COMPRESSED|^CONFIG_DEBUG_INFO_DWARF5|^CONFIG_PAHOLE" .config
time make -j"$(nproc)" bindeb-pkg KDEB_PKGVERSION=7.2.10-2mindos INSTALL_MOD_STRIP=1 >$B/build.log 2>&1
ls -la $B/*.deb
