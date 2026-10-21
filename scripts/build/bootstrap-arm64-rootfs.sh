#!/usr/bin/env bash
# MindOS Paradise: Automated ARM64 (aarch64) Rootfs & ISO Bootstrap Script
# Usage: sudo ./bootstrap-arm64-rootfs.sh [OPTIONS] <build_directory> [output.iso]
#
# Options:
#   --suite=SUITE      Debian suite name (default: trixie)
#   --mirror=MIRROR    Debian mirror URL (default: http://deb.debian.org/debian)
#   --hostname=NAME    System hostname (default: mindos-arm64)
#   --build-iso        Automatically trigger build-iso.sh once rootfs is ready
#   -h, --help         Show help message

set -euo pipefail

SUITE="trixie"
MIRROR="http://deb.debian.org/debian"
HOSTNAME="mindos-arm64"
BUILD_ISO=false
BUILD_DIR=""
OUT_ISO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --suite=*)
            SUITE="${1#*=}"
            shift ;;
        --mirror=*)
            MIRROR="${1#*=}"
            shift ;;
        --hostname=*)
            HOSTNAME="${1#*=}"
            shift ;;
        --build-iso)
            BUILD_ISO=true
            shift ;;
        -h|--help)
            echo "Usage: sudo $0 [OPTIONS] <build_directory> [output.iso]"
            echo "  --suite=SUITE      Debian suite name (default: trixie)"
            echo "  --mirror=MIRROR    Debian mirror URL (default: http://deb.debian.org/debian)"
            echo "  --hostname=NAME    System hostname (default: mindos-arm64)"
            echo "  --build-iso        Build bootable ARM64 ISO after bootstrap"
            exit 0 ;;
        *)
            if [ -z "$BUILD_DIR" ]; then
                BUILD_DIR="$1"
            elif [ -z "$OUT_ISO" ]; then
                OUT_ISO="$1"
            else
                echo "[!] Unknown argument: $1" >&2
                exit 1
            fi
            shift ;;
    esac
done

if [ -z "$BUILD_DIR" ]; then
    echo "Error: build directory is required." >&2
    echo "Usage: sudo $0 <build_directory> [output.iso]" >&2
    exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: this script must be run as root (or with sudo)." >&2
    exit 1
fi

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PARADISE_DIR=$(cd "$SCRIPT_DIR/../.." && pwd)
ROOTFS="$BUILD_DIR/rootfs"
ISO_ROOT="$BUILD_DIR/iso_root"

echo "=========================================================="
echo "🚀 MindOS ARM64 Automated Rootfs Bootstrapper"
echo "   Build Directory: $BUILD_DIR"
echo "   Suite:           $SUITE"
echo "   Mirror:          $MIRROR"
echo "   Hostname:        $HOSTNAME"
echo "=========================================================="

mkdir -p "$ROOTFS" "$ISO_ROOT" "$ISO_ROOT/live" "$ISO_ROOT/boot/grub" "$ISO_ROOT/EFI/boot" "$ISO_ROOT/.disk"

# Ensure host tools
for tool in debootstrap xorriso mksquashfs; do
    if ! command -v "$tool" &>/dev/null && [ ! -x "/usr/sbin/$tool" ]; then
        echo "[!] Required tool missing: $tool. Installing..."
        apt-get update -qq && apt-get install -y -qq "$tool"
    fi
done

DEBOOTSTRAP="/usr/sbin/debootstrap"
[ -x "$DEBOOTSTRAP" ] || DEBOOTSTRAP="debootstrap"

# Check binfmt for arm64 execution on x86_64 host
HOST_ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)
if [ "$HOST_ARCH" != "arm64" ] && [ "$HOST_ARCH" != "aarch64" ]; then
    if [ ! -f /usr/bin/qemu-aarch64-static ]; then
        echo "[*] Installing qemu-user-static and binfmt-support for cross-architecture bootstrap..."
        apt-get update -qq && apt-get install -y -qq qemu-user-static binfmt-support
    fi
fi

# Clean previous mounts on exit
cleanup_mounts() {
    for d in dev/pts dev proc sys run; do
        if mountpoint -q "$ROOTFS/$d" 2>/dev/null; then
            umount -lf "$ROOTFS/$d" 2>/dev/null || true
        fi
    done
}
trap cleanup_mounts EXIT INT TERM

# Step 1: Debootstrap ARM64
if [ ! -f "$ROOTFS/etc/debian_version" ]; then
    echo "[1/6] Running debootstrap for Debian $SUITE (arm64)..."
    CORE_PKGS="linux-image-arm64,grub-efi-arm64,systemd,systemd-sysv,live-boot,sudo,dbus,network-manager,locales,curl,wget,ca-certificates,zstd,python3"
    
    if [ "$HOST_ARCH" != "arm64" ] && [ "$HOST_ARCH" != "aarch64" ]; then
        $DEBOOTSTRAP --arch=arm64 --foreign \
            --components=main,contrib,non-free,non-free-firmware \
            --include="$CORE_PKGS" \
            "$SUITE" "$ROOTFS" "$MIRROR"
        
        cp -f /usr/bin/qemu-aarch64-static "$ROOTFS/usr/bin/"
        echo "[*] Running debootstrap second-stage via QEMU..."
        chroot "$ROOTFS" /debootstrap/debootstrap --second-stage
    else
        $DEBOOTSTRAP --arch=arm64 \
            --components=main,contrib,non-free,non-free-firmware \
            --include="$CORE_PKGS" \
            "$SUITE" "$ROOTFS" "$MIRROR"
    fi
else
    echo "[1/6] Rootfs already bootstrapped, reusing: $ROOTFS"
fi

# Step 2: Mount pseudo-filesystems
echo "[2/6] Mounting virtual filesystems for chroot..."
mount -t proc none "$ROOTFS/proc"
mount -t sysfs none "$ROOTFS/sys"
mount --bind /dev "$ROOTFS/dev"
mount --bind /dev/pts "$ROOTFS/dev/pts"

# Step 3: Base System Configuration
echo "[3/6] Configuring hostname, network, sources, and locales..."
echo "$HOSTNAME" > "$ROOTFS/etc/hostname"
cat > "$ROOTFS/etc/hosts" <<EOF
127.0.0.1   localhost
127.0.1.1   $HOSTNAME
::1         localhost ip6-localhost ip6-loopback
EOF

cat > "$ROOTFS/etc/apt/sources.list.d/debian.sources" <<EOF
Types: deb
URIs: $MIRROR
Suites: $SUITE $SUITE-updates
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

Types: deb
URIs: http://security.debian.org/debian-security
Suites: $SUITE-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
EOF

# DNS for chroot operations
cp -L /etc/resolv.conf "$ROOTFS/etc/resolv.conf" 2>/dev/null || true

# User creation (mindos:mindos)
chroot "$ROOTFS" useradd -m -s /bin/bash -G sudo,adm,dialout,audio,video mindos 2>/dev/null || true
echo "mindos:mindos" | chroot "$ROOTFS" chpasswd
echo "root:root" | chroot "$ROOTFS" chpasswd
echo "mindos ALL=(ALL) NOPASSWD:ALL" > "$ROOTFS/etc/sudoers.d/01-mindos"
chmod 0440 "$ROOTFS/etc/sudoers.d/01-mindos"

# Step 4: Integrate mindpkg and MindOS Tools
echo "[4/6] Integrating mindpkg package manager for ARM64..."
MINDPKG_SRC="$PARADISE_DIR/src/mindpkg/mindpkg"
if [ ! -f "$MINDPKG_SRC" ]; then
    MINDPKG_SRC="/usr/local/bin/mindpkg"
fi
ARCH=arm64 "$SCRIPT_DIR/integrate-mindpkg.sh" "$ROOTFS" "$MINDPKG_SRC"

# Copy branding and overlays if available
if [ -d "$PARADISE_DIR/branding" ]; then
    echo "[*] Applying MindOS Paradise branding..."
    cp -r "$PARADISE_DIR/branding/"* "$ROOTFS/" 2>/dev/null || true
fi

# Step 5: Extract Kernel and Initrd for ISO Boot
echo "[5/6] Preparing ISO live boot kernel and initrd..."
VMLINUZ=$(ls -1t "$ROOTFS/boot/vmlinuz-"* 2>/dev/null | head -n1 || true)
INITRD=$(ls -1t "$ROOTFS/boot/initrd.img-"* 2>/dev/null | head -n1 || true)

if [ -n "$VMLINUZ" ] && [ -n "$INITRD" ]; then
    cp -f "$VMLINUZ" "$ISO_ROOT/live/vmlinuz"
    cp -f "$INITRD" "$ISO_ROOT/live/initrd.img"
    echo "[✓] Kernel ($(basename "$VMLINUZ")) and Initrd ($(basename "$INITRD")) copied to live root."
else
    echo "[!] Warning: Kernel or initrd not found in rootfs/boot."
fi

# Step 6: Configure GRUB UEFI Boot for ARM64
echo "[6/6] Generating ARM64 UEFI GRUB configuration..."
cat > "$ISO_ROOT/boot/grub/grub.cfg" <<'EOF'
set default=0
set timeout=5

insmod efi_gop
insmod efi_uga
insmod video_bochs
insmod video_cirrus
insmod all_video
insmod font

if loadfont /boot/grub/fonts/unicode.pf2 ; then
    set gfxmode=auto
    insmod gfxterm
    terminal_output gfxterm
fi

menuentry "MindOS Paradise (ARM64 Live)" --class mindos --class gnu-linux --class gnu --class os {
    linux /live/vmlinuz boot=live components quiet splash systemd.mask=plymouth-start.service console=ttyAMA0,115200 console=tty0
    initrd /live/initrd.img
}

menuentry "MindOS Paradise (ARM64 Safe Graphics)" --class mindos --class gnu-linux {
    linux /live/vmlinuz boot=live components nomodeset console=ttyAMA0,115200 console=tty0
    initrd /live/initrd.img
}
EOF

# Clean up mounts before finishing
cleanup_mounts

# Remove host qemu binary from rootfs if we injected it
if [ "$HOST_ARCH" != "arm64" ] && [ "$HOST_ARCH" != "aarch64" ]; then
    rm -f "$ROOTFS/usr/bin/qemu-aarch64-static"
fi

echo "=========================================================="
echo "✅ ARM64 Rootfs & ISO Environment Ready!"
echo "   Rootfs:   $ROOTFS"
echo "   ISO Root: $ISO_ROOT"
echo "=========================================================="

if [ "$BUILD_ISO" = true ]; then
    OUT_ISO="${OUT_ISO:-$BUILD_DIR/mindos-paradise-arm64.iso}"
    echo "🔨 Triggering automated ISO build: $OUT_ISO"
    ARCH=arm64 "$SCRIPT_DIR/build-iso.sh" "$BUILD_DIR" "$OUT_ISO" "arm64"
    echo "🎉 ARM64 ISO generation finished: $OUT_ISO"
fi
