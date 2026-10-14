#!/usr/bin/env bash
# MindOS Paradise kernel config optimizasyonu (Debian 6.12 config tabanı -> 7.2.x)
set -e
cd "${1:?kernel kaynak dizini}"
C=scripts/config

# Kimlik: uname -r -> 7.2.10-mindos
$C --set-str LOCALVERSION "-mindos" -d LOCALVERSION_AUTO

# Debian'a özel imza anahtarları / modül imzası kapat (derleme hatası + boyut)
$C --set-str SYSTEM_TRUSTED_KEYS "" --set-str SYSTEM_REVOCATION_KEYS "" -d MODULE_SIG -d MODULE_SIG_ALL

# Debug sembolleri kapalı -> çok daha küçük modüller, hızlı derleme
$C -d DEBUG_INFO -d DEBUG_INFO_DWARF5 -d DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT -d DEBUG_INFO_BTF -e DEBUG_INFO_NONE

# Masaüstü tepkiselliği: tam preempt + 1000Hz
$C -d PREEMPT_VOLUNTARY -e PREEMPT -e PREEMPT_DYNAMIC
$C -d HZ_250 -e HZ_1000 --set-val HZ 1000

# Sıkıştırma: zstd (hızlı açılış, küçük boyut)
$C -d KERNEL_GZIP -d KERNEL_XZ -e KERNEL_ZSTD
$C -d MODULE_COMPRESS_XZ -e MODULE_COMPRESS_ZSTD -e MODULE_COMPRESS_ALL -e MODULE_DECOMPRESS

# RAM: zswap varsayılan açık (zstd), zram zstd, MGLRU, THP sadece madvise
$C -e ZSWAP -e ZSWAP_DEFAULT_ON -e ZSWAP_SHRINKER_DEFAULT_ON \
   -d ZSWAP_COMPRESSOR_DEFAULT_LZO -e ZSWAP_COMPRESSOR_DEFAULT_ZSTD --set-str ZSWAP_COMPRESSOR_DEFAULT zstd
$C -m ZRAM -d ZRAM_DEF_COMP_LZ4 -e ZRAM_DEF_COMP_ZSTD --set-str ZRAM_DEF_COMP zstd
$C -e LRU_GEN -e LRU_GEN_ENABLED
$C -d TRANSPARENT_HUGEPAGE_ALWAYS -e TRANSPARENT_HUGEPAGE_MADVISE
$C -e KSM
# Statik per-cpu bellek yükünü azalt (Debian: 8192)
$C -d MAXSMP --set-val NR_CPUS 512

# Masaüstünde gereksiz sunucu/egzotik donanım alt sistemleri (boyut)
for o in STAGING INFINIBAND HAMRADIO ATM ISDN CAN ARCNET FDDI WAN IEEE802154 6LOWPAN \
         RAPIDIO GREYBUS MEDIA_DIGITAL_TV_SUPPORT MEDIA_ANALOG_TV_SUPPORT MEDIA_SDR_SUPPORT \
         MLX4_CORE MLX5_CORE NET_VENDOR_CHELSIO NET_VENDOR_HUAWEI NET_VENDOR_CAVIUM \
         SCSI_DEBUG KUNIT RUNTIME_TESTING_MENU X86_NATIVE_CPU; do
  $C -d $o
done
