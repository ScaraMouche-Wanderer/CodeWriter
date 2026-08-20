#!/usr/bin/env bash
# CodeWriter desktop installer script
# Installs desktop launcher, app-id mappings, and HD raster/vector icons to ~/.local/share/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_EXEC="$(which python3)"
APP_ENTRY="${PROJECT_ROOT}/app.py"
ICON_SRC="${PROJECT_ROOT}/resources/icons/codewriter.svg"

APPS_DIR="${HOME}/.local/share/applications"
ICONS_BASE="${HOME}/.local/share/icons/hicolor"
PIXMAPS_DIR="${HOME}/.local/share/pixmaps"

echo "==> Installing CodeWriter..."
echo "    Project Root: ${PROJECT_ROOT}"
echo "    Python Exec:  ${PYTHON_EXEC}"

# Ensure directories exist
mkdir -p "${APPS_DIR}"
mkdir -p "${ICONS_BASE}/scalable/apps"
mkdir -p "${PIXMAPS_DIR}"

# Remove duplicate or obsolete desktop entries if present
rm -f "${APPS_DIR}/codewriter.desktop"
rm -f "${APPS_DIR}/codetyper.desktop"
rm -f "${ICONS_BASE}/scalable/apps/codetyper.svg"
rm -f "${PIXMAPS_DIR}/codetyper.svg"

# 1. Install Scalable Vector Icons for both codewriter and com.local.codewriter
cp -f "${ICON_SRC}" "${ICONS_BASE}/scalable/apps/codewriter.svg"
cp -f "${ICON_SRC}" "${ICONS_BASE}/scalable/apps/com.local.codewriter.svg"
cp -f "${ICON_SRC}" "${PIXMAPS_DIR}/codewriter.svg"
cp -f "${ICON_SRC}" "${PIXMAPS_DIR}/com.local.codewriter.svg"
echo "    Installed SVG icons for codewriter and com.local.codewriter."

# 2. Generate and install Multi-Size PNG Icons for Wayland / GNOME Shell / Taskbar Dock / System Tray
SIZES=(16 24 32 48 64 128 256 512)
if command -v rsvg-convert >/dev/null 2>&1; then
    for size in "${SIZES[@]}"; do
        size_dir="${ICONS_BASE}/${size}x${size}/apps"
        mkdir -p "${size_dir}"
        rsvg-convert -w "${size}" -h "${size}" "${ICON_SRC}" -o "${size_dir}/codewriter.png"
        rsvg-convert -w "${size}" -h "${size}" "${ICON_SRC}" -o "${size_dir}/com.local.codewriter.png"
    done
    rsvg-convert -w 256 -h 256 "${ICON_SRC}" -o "${PIXMAPS_DIR}/codewriter.png"
    rsvg-convert -w 256 -h 256 "${ICON_SRC}" -o "${PIXMAPS_DIR}/com.local.codewriter.png"
    echo "    Generated multi-resolution PNG icons (16x16 to 512x512) for both IDs."
fi

# 3. Generate Single Canonical Desktop Entry (com.local.codewriter.desktop)
DESKTOP_CONTENT="[Desktop Entry]
Type=Application
Name=CodeWriter
GenericName=Keystroke Simulation Utility
Comment=Native Linux keystroke automation & typing utility for developers
Exec=${PYTHON_EXEC} ${APP_ENTRY}
Icon=codewriter
Terminal=false
Categories=Utility;Development;
StartupNotify=true
StartupWMClass=com.local.codewriter
X-GNOME-UsesNotifications=true
"

echo "${DESKTOP_CONTENT}" > "${APPS_DIR}/com.local.codewriter.desktop"
chmod 644 "${APPS_DIR}/com.local.codewriter.desktop"
chmod +x "${APP_ENTRY}"
echo "    Installed canonical desktop entry (com.local.codewriter.desktop)."


# 4. Refresh Desktop & Icon Databases
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APPS_DIR}" >/dev/null 2>&1 || true
    echo "    Updated desktop database."
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${ICONS_BASE}" >/dev/null 2>&1 || true
    echo "    Updated icon cache."
fi

echo ""
echo "==> CodeWriter installation & icon sync complete!"
echo "    The CodeWriter icon is now synced to your GNOME Dock, App Switcher, System Tray, and Launcher."
