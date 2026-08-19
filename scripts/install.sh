#!/usr/bin/env bash
# CodeTyper desktop installer script
# Installs desktop launcher and icons to ~/.local/share/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_EXEC="$(which python3)"
APP_ENTRY="${PROJECT_ROOT}/app.py"
ICON_SRC="${PROJECT_ROOT}/resources/icons/codetyper.svg"

APPS_DIR="${HOME}/.local/share/applications"
ICONS_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"
DESKTOP_TARGET="${APPS_DIR}/codetyper.desktop"
ICON_TARGET="${ICONS_DIR}/codetyper.svg"

echo "==> Installing CodeTyper..."
echo "    Project Root: ${PROJECT_ROOT}"
echo "    Python Exec:  ${PYTHON_EXEC}"

# Ensure directories exist
mkdir -p "${APPS_DIR}"
mkdir -p "${ICONS_DIR}"

# Install icon
cp -f "${ICON_SRC}" "${ICON_TARGET}"
echo "    Installed icon to: ${ICON_TARGET}"

# Generate and install desktop file
cat > "${DESKTOP_TARGET}" <<EOF
[Desktop Entry]
Type=Application
Name=CodeTyper
Comment=Type code into any focused application via simulated keystrokes
Exec=${PYTHON_EXEC} ${APP_ENTRY}
Icon=${ICON_TARGET}
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF

chmod 644 "${DESKTOP_TARGET}"
chmod +x "${APP_ENTRY}"
echo "    Installed desktop entry to: ${DESKTOP_TARGET}"

# Update desktop database if tool is present
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${APPS_DIR}" >/dev/null 2>&1 || true
    echo "    Updated desktop database."
fi

# Update icon cache if tool is present
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo ""
echo "==> CodeTyper installation complete!"
echo "    You can now launch 'CodeTyper' directly from your application launcher or GNOME App Grid."
