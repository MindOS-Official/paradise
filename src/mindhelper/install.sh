#!/bin/bash
# ==============================================================================
# Mind Helper — System Integration Installer for MindOS Paradise
# Integrates Mind Helper directly into the system root or a custom root filesystem.
# ==============================================================================
set -e

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_ROOT="${1:-}"

if [ -n "$TARGET_ROOT" ] && [ -d "$TARGET_ROOT" ]; then
    echo "✦ Target Root specified: $TARGET_ROOT"
    PREFIX="$TARGET_ROOT"
else
    PREFIX=""
fi

echo "✦ Installing Mind Helper into system tree (${PREFIX:-/})..."

# Ensure destination directories exist
mkdir -p "${PREFIX}/usr/share/mindhelper/assets"
mkdir -p "${PREFIX}/usr/share/applications"
mkdir -p "${PREFIX}/etc/xdg/autostart"
mkdir -p "${PREFIX}/etc/skel/.config/autostart"
mkdir -p "${PREFIX}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${PREFIX}/var/log/mindos" && chmod 777 "${PREFIX}/var/log/mindos" || true

# Copy Python modules & styling
echo "• Installing application modules and styling..."
cp "${SRC_DIR}"/*.py "${PREFIX}/usr/share/mindhelper/"
cp "${SRC_DIR}/style.css" "${PREFIX}/usr/share/mindhelper/"
cp -r "${SRC_DIR}/assets"/* "${PREFIX}/usr/share/mindhelper/assets/"

# Install executable launcher
echo "• Installing /usr/bin/mindhelper launcher..."
cp "${SRC_DIR}/mindhelper" "${PREFIX}/usr/bin/mindhelper"
chmod +x "${PREFIX}/usr/bin/mindhelper"
chmod +x "${PREFIX}/usr/share/mindhelper/"*.py

# Install scalable and raster icons
echo "• Registering system icons..."
mkdir -p "${PREFIX}/usr/share/pixmaps"
cp "${SRC_DIR}/assets/mindhelper.svg" "${PREFIX}/usr/share/icons/hicolor/scalable/apps/mindhelper.svg" 2>/dev/null || true
if [ -f "${SRC_DIR}/assets/mindhelper.png" ]; then
    cp "${SRC_DIR}/assets/mindhelper.png" "${PREFIX}/usr/share/pixmaps/mindhelper.png"
fi
for s in 16 22 24 32 36 48 64 72 96 128 192 256 512; do
    if [ -f "${SRC_DIR}/assets/icons/${s}x${s}/mindhelper.png" ]; then
        mkdir -p "${PREFIX}/usr/share/icons/hicolor/${s}x${s}/apps"
        cp "${SRC_DIR}/assets/icons/${s}x${s}/mindhelper.png" "${PREFIX}/usr/share/icons/hicolor/${s}x${s}/apps/mindhelper.png"
    fi
done

# Install Desktop & Autostart entries
echo "• Registering desktop and autostart entries..."
cp "${SRC_DIR}/mindhelper.desktop" "${PREFIX}/usr/share/applications/mindhelper.desktop"
cp "${SRC_DIR}/mindhelper-autostart.desktop" "${PREFIX}/etc/xdg/autostart/mindhelper-autostart.desktop"
cp "${SRC_DIR}/mindhelper-autostart.desktop" "${PREFIX}/etc/skel/.config/autostart/mindhelper-autostart.desktop"

# Backward compatibility symlink for mindbot
if [ ! -e "${PREFIX}/usr/bin/mindbot" ]; then
    ln -s /usr/bin/mindhelper "${PREFIX}/usr/bin/mindbot" 2>/dev/null || true
fi

# Update desktop & icon caches if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${PREFIX}/usr/share/applications" 2>/dev/null || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${PREFIX}/usr/share/icons/hicolor" 2>/dev/null || true
fi

echo "✦ Mind Helper installation completed successfully."
echo "✦ Mind Helper is ready to awaken with MindOS Paradise."
