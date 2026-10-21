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
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

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
for tool in debootstrap xorriso mksquashfs mkfs.vfat mcopy; do
    if ! command -v "$tool" &>/dev/null && [ ! -x "/usr/sbin/$tool" ] && [ ! -x "/sbin/$tool" ]; then
        echo "[!] Required tool missing: $tool. Installing..."
        apt-get update -qq && apt-get install -y -qq "$tool" || true
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
    CORE_PKGS="linux-image-arm64,grub-efi-arm64,systemd,systemd-sysv,live-boot,sudo,dbus,network-manager,locales,curl,wget,ca-certificates,zstd,python3,openssl"
    
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
if ! chroot "$ROOTFS" id -u mindos &>/dev/null; then
    chroot "$ROOTFS" useradd -m -s /bin/bash mindos
fi
for grp in sudo adm dialout audio video plugdev netdev cdrom; do
    chroot "$ROOTFS" usermod -aG "$grp" mindos 2>/dev/null || true
done
echo "mindos:mindos" | chroot "$ROOTFS" chpasswd
echo "root:root" | chroot "$ROOTFS" chpasswd
echo "mindos ALL=(ALL) NOPASSWD:ALL" > "$ROOTFS/etc/sudoers.d/01-mindos"
chmod 0440 "$ROOTFS/etc/sudoers.d/01-mindos"

# Locale generation
if [ -f "$ROOTFS/etc/locale.gen" ]; then
    sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' "$ROOTFS/etc/locale.gen" 2>/dev/null || true
    sed -i 's/^# *tr_TR.UTF-8 UTF-8/tr_TR.UTF-8 UTF-8/' "$ROOTFS/etc/locale.gen" 2>/dev/null || true
    chroot "$ROOTFS" locale-gen 2>/dev/null || true
fi
echo "LANG=en_US.UTF-8" > "$ROOTFS/etc/default/locale"

# Step 3b: Install Complete MindOS Paradise Desktop Suite
echo "[3b/6] Installing GNOME 48, GDM3, Pipewire, Calamares, Plymouth, and desktop apps..."
cat > "$ROOTFS/etc/apt/apt.conf.d/99mindos-install" <<'EOF'
APT::Install-Recommends "0";
APT::Install-Suggests "0";
EOF

# Remove legacy sources.list if generated by debootstrap to avoid duplicate source warnings
rm -f "$ROOTFS/etc/apt/sources.list"

DEBIAN_FRONTEND=noninteractive chroot "$ROOTFS" apt-get update -qq

DESKTOP_PKGS=(
    gnome-core
    gnome-shell
    gdm3
    gnome-control-center
    gnome-terminal
    gnome-text-editor
    gnome-system-monitor
    nautilus
    gnome-disk-utility
    gnome-tweaks
    gnome-shell-extension-manager
    gnome-shell-extension-dashtodock
    gnome-shell-extension-arc-menu
    gnome-shell-extension-desktop-icons-ng
    pipewire
    pipewire-audio
    wireplumber
    pipewire-pulse
    pipewire-alsa
    network-manager
    wpasupplicant
    wireless-regdb
    calamares
    calamares-settings-debian
    plymouth
    plymouth-themes
    plymouth-label
    fastfetch
    python3-gi
    python3-cairo
    python3-psutil
    python3-requests
    gir1.2-gtk-3.0
    gir1.2-gtk-4.0
    gir1.2-adw-1
    gir1.2-notify-0.7
    pkexec
    unattended-upgrades
    rfkill
    nftables
    systemd-timesyncd
    firmware-linux-free
    adwaita-icon-theme
    fonts-dejavu-core
    fonts-cantarell
    live-boot-initramfs-tools
    live-config
    live-config-systemd
)

DEBIAN_FRONTEND=noninteractive chroot "$ROOTFS" apt-get install -y "${DESKTOP_PKGS[@]}"
rm -f "$ROOTFS/etc/apt/apt.conf.d/99mindos-install"

# Install apple-bcm-firmware deb package if available (Apple Silicon Wi-Fi & Bluetooth)
BCM_DEB=$(ls -1t "$PARADISE_DIR"/../paradise-build/release/apple-bcm-firmware_*.deb "$PARADISE_DIR"/packages/apple-bcm-firmware_*.deb 2>/dev/null | head -n1 || true)
if [ -n "$BCM_DEB" ] && [ -f "$BCM_DEB" ]; then
    echo "[*] Installing Apple Silicon firmware bundle ($BCM_DEB)..."
    cp -f "$BCM_DEB" "$ROOTFS/tmp/apple-bcm-firmware.deb"
    DEBIAN_FRONTEND=noninteractive chroot "$ROOTFS" dpkg -i /tmp/apple-bcm-firmware.deb || DEBIAN_FRONTEND=noninteractive chroot "$ROOTFS" apt-get install -fy
    rm -f "$ROOTFS/tmp/apple-bcm-firmware.deb"
fi

# Install mindos-apps deb package if available
APPS_DEB=$(ls -1t "$PARADISE_DIR"/../paradise-build/release/mindos-apps_*_all.deb 2>/dev/null | head -n1 || true)
if [ -n "$APPS_DEB" ] && [ -f "$APPS_DEB" ]; then
    echo "[*] Installing MindOS applications bundle ($APPS_DEB)..."
    cp -f "$APPS_DEB" "$ROOTFS/tmp/mindos-apps.deb"
    DEBIAN_FRONTEND=noninteractive chroot "$ROOTFS" dpkg -i /tmp/mindos-apps.deb || DEBIAN_FRONTEND=noninteractive chroot "$ROOTFS" apt-get install -fy
    rm -f "$ROOTFS/tmp/mindos-apps.deb"
fi

# Step 4: Integrate mindpkg and MindOS Tools
echo "[4/6] Integrating mindpkg package manager and desktop overlays for ARM64..."
MINDPKG_SRC="$PARADISE_DIR/src/mindpkg/mindpkg"
if [ ! -f "$MINDPKG_SRC" ]; then
    MINDPKG_SRC="/usr/local/bin/mindpkg"
fi
ARCH=arm64 "$SCRIPT_DIR/integrate-mindpkg.sh" "$ROOTFS" "$MINDPKG_SRC"

# Copy overlays (Mind Arc, Mind Helper, extensions, dconf, etc.)
if [ -d "$PARADISE_DIR/overlay" ]; then
    echo "[*] Applying MindOS Paradise system overlay..."
    cp -a "$PARADISE_DIR/overlay/." "$ROOTFS/"
fi

# Copy src applications
if [ -d "$PARADISE_DIR/src/mind-arc" ]; then
    mkdir -p "$ROOTFS/opt/mind-arc"
    rsync -a --delete "$PARADISE_DIR/src/mind-arc/" "$ROOTFS/opt/mind-arc/"
    chmod +x "$ROOTFS/opt/mind-arc/main.py" "$ROOTFS/opt/mind-arc/mindarc_extra.py" 2>/dev/null || true
fi

if [ -d "$PARADISE_DIR/src/mindhelper" ]; then
    mkdir -p "$ROOTFS/usr/share/mindhelper"
    rsync -a --delete "$PARADISE_DIR/src/mindhelper/" "$ROOTFS/usr/share/mindhelper/"
fi

# Shell extensions
EXT_DIR="$ROOTFS/usr/share/gnome-shell/extensions"
mkdir -p "$EXT_DIR"
for ext in "$PARADISE_DIR"/src/shell-extension/*@* "$PARADISE_DIR"/third_party/*@*; do
    if [ -d "$ext" ]; then
        ext_name=$(basename "$ext")
        mkdir -p "$EXT_DIR/$ext_name"
        rsync -a --delete "$ext/" "$EXT_DIR/$ext_name/"
    fi
done

# Copy blur-my-shell schema
if [ -d "$PARADISE_DIR/third_party/blur-my-shell@aunetx/schemas" ]; then
    cp -f "$PARADISE_DIR"/third_party/blur-my-shell@aunetx/schemas/*.gschema.xml "$ROOTFS/usr/share/glib-2.0/schemas/" 2>/dev/null || true
fi

# Copy branding assets (wallpapers, icons, logos)
BRANDING_SRC="$PARADISE_DIR/branding"
[ -d "$BRANDING_SRC" ] || BRANDING_SRC="$PARADISE_DIR/../paradise-build/branding"

if [ -d "$BRANDING_SRC" ]; then
    echo "[*] Applying MindOS Paradise branding, wallpapers, and icons..."
    mkdir -p "$ROOTFS/usr/share/backgrounds" "$ROOTFS/usr/share/mindos" "$ROOTFS/usr/share/mindos/avatar" "$ROOTFS/usr/share/mindos/icons"
    if [ -f "$BRANDING_SRC/out/mindos-wallpaper.jpg" ]; then
        cp -f "$BRANDING_SRC/out/mindos-wallpaper.jpg" "$ROOTFS/usr/share/backgrounds/mindos-wallpaper.jpg"
        cp -f "$BRANDING_SRC/out/mindos-wallpaper.jpg" "$ROOTFS/usr/share/mindos/mindos-wallpaper.jpg"
    fi
    if [ -f "$BRANDING_SRC/out/mindos-avatar.png" ]; then
        cp -f "$BRANDING_SRC/out/mindos-avatar.png" "$ROOTFS/usr/share/mindos/avatar/mindos-avatar.png"
    fi
    if [ -f "$BRANDING_SRC/out/mindos-d12.png" ]; then
        cp -f "$BRANDING_SRC/out/mindos-d12.png" "$ROOTFS/usr/share/mindos/icons/mindos-d12.png"
    fi
    for sz in 16 24 32 48 64 128 256 512; do
        if [ -f "$BRANDING_SRC/out/mind-arc-$sz.png" ]; then
            install -Dm644 "$BRANDING_SRC/out/mind-arc-$sz.png" "$ROOTFS/usr/share/icons/hicolor/${sz}x${sz}/apps/mind-arc.png"
        fi
    done
fi

# Set default plymouth theme
if [ -d "$ROOTFS/usr/share/plymouth/themes/mindos" ]; then
    chroot "$ROOTFS" plymouth-set-default-theme -R mindos 2>/dev/null || true
fi

# Compile schemas and update dconf
chroot "$ROOTFS" glib-compile-schemas /usr/share/glib-2.0/schemas 2>/dev/null || true
chroot "$ROOTFS" dconf update 2>/dev/null || true

# Enable services
chroot "$ROOTFS" systemctl enable gdm3 NetworkManager systemd-timesyncd 2>/dev/null || true

# Step 5: Generate Initrd and Extract Kernel for ISO Boot
echo "[5/6] Preparing ISO live boot kernel and initrd..."
echo "[*] Ensuring live-boot support in initramfs..."
chroot "$ROOTFS" update-initramfs -u -k all 2>/dev/null || chroot "$ROOTFS" update-initramfs -c -k all 2>/dev/null || true

VMLINUZ=$(ls -1t "$ROOTFS/boot/vmlinuz-"* 2>/dev/null | head -n1 || true)
INITRD=$(ls -1t "$ROOTFS/boot/initrd.img-"* 2>/dev/null | head -n1 || true)

if [ -n "$VMLINUZ" ] && [ -n "$INITRD" ]; then
    cp -f "$VMLINUZ" "$ISO_ROOT/live/vmlinuz"
    cp -f "$INITRD" "$ISO_ROOT/live/initrd.img"
    echo "[✓] Kernel ($(basename "$VMLINUZ")) and Initrd ($(basename "$INITRD")) copied to live root."
else
    echo "[!] Warning: Kernel or initrd not found in rootfs/boot."
fi

# Stage Device Tree Blobs (DTB) for Apple Silicon, Raspberry Pi 4/5, Snapdragon X Elite
echo "[*] Staging Device Tree Blobs (DTB) for live ARM64 boot..."
mkdir -p "$ISO_ROOT/boot/dtbs" "$ISO_ROOT/live"
for dtb_src in "$ROOTFS"/usr/lib/linux-image-*/apple "$ROOTFS"/usr/lib/linux-image-*/broadcom \
               "$ROOTFS"/usr/lib/linux-image-*/qcom "$ROOTFS"/boot/dtbs* "$ROOTFS"/usr/lib/firmware; do
    if [ -d "$dtb_src" ]; then
        cp -rf "$dtb_src" "$ISO_ROOT/boot/dtbs/" 2>/dev/null || true
    fi
done
# Ensure flat DTB references are also accessible
find "$ISO_ROOT/boot/dtbs" -mindepth 2 -name "*.dtb" -exec cp -u {} "$ISO_ROOT/boot/dtbs/" \; 2>/dev/null || true

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
insmod serial

serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1
terminal_input console serial
terminal_output console serial

if loadfont /boot/grub/fonts/unicode.pf2 ; then
    set gfxmode=auto
    insmod gfxterm
    terminal_output gfxterm serial
fi

menuentry "MindOS Paradise (ARM64 Live - UEFI / Auto)" --class mindos --class gnu-linux --class gnu --class os {
    linux /live/vmlinuz boot=live components quiet splash console=tty0 console=ttyAMA0,115200
    initrd /live/initrd.img
    if [ -n "${devicetree_path}" ]; then
        devicetree ${devicetree_path}
    elif [ -f /boot/dtb ]; then
        devicetree /boot/dtb
    elif [ -f /live/dtb.img ]; then
        devicetree /live/dtb.img
    elif [ -f /live/devicetree ]; then
        devicetree /live/devicetree
    fi
}

menuentry "MindOS Paradise (Apple Silicon M1/M2)" --class mindos --class apple --class gnu-linux {
    linux /live/vmlinuz boot=live components quiet splash apple_dcp.modeset=1 console=tty0 console=ttyAMA0,115200
    initrd /live/initrd.img
    if [ -n "${devicetree_path}" ]; then
        devicetree ${devicetree_path}
    elif [ -f /boot/dtbs/apple/t8103-j274.dtb ]; then
        devicetree /boot/dtbs/apple/t8103-j274.dtb
    elif [ -f /live/apple.dtb ]; then
        devicetree /live/apple.dtb
    fi
}

menuentry "MindOS Paradise (Raspberry Pi 4 / 5)" --class mindos --class rpi --class gnu-linux {
    linux /live/vmlinuz boot=live components quiet splash console=tty0 console=ttyAMA0,115200
    initrd /live/initrd.img
    if [ -n "${devicetree_path}" ]; then
        devicetree ${devicetree_path}
    elif [ -f /boot/dtbs/broadcom/bcm2712-rpi-5-b.dtb ]; then
        devicetree /boot/dtbs/broadcom/bcm2712-rpi-5-b.dtb
    elif [ -f /boot/dtbs/broadcom/bcm2711-rpi-4-b.dtb ]; then
        devicetree /boot/dtbs/broadcom/bcm2711-rpi-4-b.dtb
    elif [ -f /live/rpi.dtb ]; then
        devicetree /live/rpi.dtb
    fi
}

menuentry "MindOS Paradise (Snapdragon X Elite / Laptop)" --class mindos --class qualcomm --class gnu-linux {
    linux /live/vmlinuz boot=live components quiet splash pd_ignore_unused clk_ignore_unused console=tty0 console=ttyAMA0,115200
    initrd /live/initrd.img
    if [ -n "${devicetree_path}" ]; then
        devicetree ${devicetree_path}
    elif [ -f /boot/dtbs/qcom/x1e80100-crd.dtb ]; then
        devicetree /boot/dtbs/qcom/x1e80100-crd.dtb
    fi
}

menuentry "MindOS Paradise (ARM64 Safe Graphics)" --class mindos --class gnu-linux {
    linux /live/vmlinuz boot=live components nomodeset console=tty0 console=ttyAMA0,115200
    initrd /live/initrd.img
    if [ -n "${devicetree_path}" ]; then
        devicetree ${devicetree_path}
    fi
}
EOF


# Clean up apt caches and host resolv.conf
chroot "$ROOTFS" apt-get clean 2>/dev/null || true
rm -rf "$ROOTFS"/var/lib/apt/lists/*
rm -f "$ROOTFS/etc/resolv.conf"
ln -sf /run/systemd/resolve/stub-resolv.conf "$ROOTFS/etc/resolv.conf" 2>/dev/null || true

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
