#!/usr/bin/env bash
# MindOS Paradise rootfs'ine mindpkg entegrasyonu
# kullanım: sudo integrate-mindpkg.sh <rootfs_dizini> [mindpkg_binary]
set -e
R="${1:?rootfs dizini gerekli}"
SRC="${2:-/usr/local/bin/mindpkg}"
[ -d "$R/usr" ] || { echo "Geçersiz rootfs: $R"; exit 1; }

# 1) Çekirdek binary
install -Dm755 "$SRC" "$R/usr/local/bin/mindpkg"

# 2) Yapılandırma: yalnızca resmi GitHub deposu (geliştirici makinesine özel yerel yollar ISO'ya girmez)
install -d "$R/etc/mindpkg/repos.d"
cat > "$R/etc/mindpkg/mindpkg.conf" <<'C'
{
    "architecture": "x86_64",
    "cache_dir": "/var/cache/mindpkg/pkg",
    "repositories": [
        {
            "name": "official",
            "url": "https://raw.githubusercontent.com/MindOS-Official/packages/main",
            "enabled": true
        }
    ]
}
C

# 3) Veritabanı ve önbellek dizinleri
install -d "$R/var/lib/mindpkg/installed" "$R/var/lib/mindpkg/repos" "$R/var/cache/mindpkg/pkg"

# 4) Bash tamamlama
install -Dm644 /dev/stdin "$R/usr/share/bash-completion/completions/mindpkg" <<'B'
# mindpkg bash completion (MindOS)
_mindpkg() {
    local cur prev cmds
    cur="${COMP_WORDS[COMP_CWORD]}"; prev="${COMP_WORDS[1]}"
    cmds="install remove update upgrade search list info build clean version"
    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "$cmds" -- "$cur") ); return
    fi
    case "$prev" in
        remove|rm|del|uninstall|info|show)
            COMPREPLY=( $(compgen -W "$(ls /var/lib/mindpkg/installed 2>/dev/null | sed 's/\.json$//')" -- "$cur") ) ;;
        install|add|i)
            local names
            names=$(python3 -c 'import json,glob
for f in glob.glob("/var/lib/mindpkg/repos/*.json"):
    try: print(" ".join(p["name"] for p in json.load(open(f)).get("packages",[])))
    except Exception: pass' 2>/dev/null)
            COMPREPLY=( $(compgen -W "$names" -- "$cur") $(compgen -f -X '!*.mind' -- "$cur") ) ;;
        build) COMPREPLY=( $(compgen -d -- "$cur") ) ;;
    esac
}
complete -F _mindpkg mindpkg
B

# 5) Depo indeksini önceden çek (ISO ilk açılışta da paket listesi hazır olsun; ağ yoksa sessizce geçer)
if [ -e "$R/etc/resolv.conf" ]; then
    chroot "$R" /usr/local/bin/mindpkg update || echo "[!] mindpkg update başarısız (ağ yok?) - ilk açılışta yapılabilir"
fi
echo "[✓] mindpkg rootfs'e entegre edildi: $R"
