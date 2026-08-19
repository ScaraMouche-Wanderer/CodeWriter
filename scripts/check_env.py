#!/usr/bin/env python3
"""
Environment and dependency validation script for CodeTyper.
Checks Python version, PyGObject, GTK4, GtkSourceView 5, and ydotool reachability.
"""

import os
import shutil
import subprocess
import sys
from typing import List, Tuple


def get_distro_id() -> str:
    """Attempt to detect the Linux distribution ID."""
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.strip().split("=", 1)[1].strip('"\'').lower()
    return "unknown"


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is >= 3.10."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 10):
        return True, f"Python {version_str} (>= 3.10 required)"
    return False, f"Python {version_str} is installed, but >= 3.10 is required"


def check_pygobject_and_gtk() -> Tuple[bool, str, List[str]]:
    """Check PyGObject, GTK 4.0, and GtkSourceView 5."""
    missing_hints = []
    distro = get_distro_id()

    # Determine package manager recommendations
    if distro in ("debian", "ubuntu", "pop", "mint", "kali"):
        install_cmd = "sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-gtksource-5"
    elif distro in ("arch", "manjaro", "endeavouros"):
        install_cmd = "sudo pacman -S python-gobject gtk4 gtksourceview5"
    elif distro in ("fedora", "rhel", "centos"):
        install_cmd = "sudo dnf install python3-gobject gtk4 gtksourceview5"
    else:
        install_cmd = "Install python3-gi, GTK4 GObject introspection bindings, and gtksourceview5 via your package manager."

    try:
        import gi
    except ImportError as e:
        missing_hints.append(f"PyGObject missing ({e}). Run: {install_cmd}")
        return False, "PyGObject (gi) not found", missing_hints

    # Check GTK 4.0
    try:
        gi.require_version("Gtk", "4.0")
        from gi.repository import Gtk  # noqa: F401
    except Exception as e:
        missing_hints.append(f"GTK 4.0 bindings missing ({e}). Run: {install_cmd}")
        return False, f"GTK 4.0 unavailable: {e}", missing_hints

    # Check GtkSourceView 5
    try:
        gi.require_version("GtkSource", "5")
        from gi.repository import GtkSource  # noqa: F401
    except Exception as e:
        missing_hints.append(f"GtkSourceView 5 bindings missing ({e}). Run: {install_cmd}")
        return False, f"GtkSourceView 5 unavailable: {e}", missing_hints

    return True, "PyGObject, GTK 4.0, and GtkSourceView 5 available", []


def check_ydotool() -> Tuple[bool, str, List[str]]:
    """Check if ydotool binary is installed and ydotoold socket is reachable."""
    hints = []
    distro = get_distro_id()

    if distro in ("debian", "ubuntu", "pop", "mint", "kali"):
        ydotool_pkg = "sudo apt install ydotool"
    elif distro in ("arch", "manjaro", "endeavouros"):
        ydotool_pkg = "sudo pacman -S ydotool"
    elif distro in ("fedora", "rhel", "centos"):
        ydotool_pkg = "sudo dnf install ydotool"
    else:
        ydotool_pkg = "Install ydotool package via your distro package manager."

    binary_path = shutil.which("ydotool")
    if not binary_path:
        hints.append(f"ydotool binary not found in PATH. Install it using:\n  {ydotool_pkg}")
        return False, "ydotool binary missing", hints

    # Check ydotoold reachability
    socket_candidates = [
        os.environ.get("YDOTOOL_SOCKET"),
        f"/run/user/{os.getuid()}/.ydotool_socket",
        "/tmp/.ydotool_socket",
        "/run/ydotoold/ydotoold.socket",
    ]
    accessible_socket = None
    for path in socket_candidates:
        if path and os.path.exists(path):
            accessible_socket = path
            break

    # Check if daemon process is running
    is_daemon_running = False
    try:
        ps_res = subprocess.run(["pgrep", "-a", "ydotoold"], capture_output=True, text=True)
        if ps_res.returncode == 0 and ps_res.stdout.strip():
            is_daemon_running = True
    except Exception:
        pass

    # Test basic communication via safe non-typing invocation
    is_reachable = False
    try:
        res = subprocess.run(
            ["ydotool", "mousemove", "--", "0", "0"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            is_reachable = True
    except Exception:
        pass

    if not is_reachable:
        daemon_hints = (
            "ydotoold daemon does not appear to be running or socket is not accessible.\n"
            "To start the daemon, run:\n"
            "  systemctl --user start ydotoold  # if systemd unit is available\n"
            "  OR\n"
            "  ydotoold &\n"
            "Ensure your user is in the 'input' group: sudo usermod -aG input $USER"
        )
        hints.append(daemon_hints)
        return False, "ydotoold daemon unreachable", hints

    detail_str = f"Installed ({binary_path})"
    if accessible_socket:
        detail_str += f", socket at {accessible_socket}"
    elif is_daemon_running:
        detail_str += ", daemon running"

    return True, f"ydotool & ydotoold: {detail_str}", []


def main() -> int:
    print("=" * 60)
    print(" CodeTyper — Environment & Dependency Check (Phase 0)")
    print("=" * 60)

    all_passed = True
    action_items: List[str] = []

    # 1. Python version check
    py_ok, py_msg = check_python_version()
    status_py = "[ PASS ]" if py_ok else "[ FAIL ]"
    print(f"{status_py} Python: {py_msg}")
    if not py_ok:
        all_passed = False
        action_items.append("Upgrade Python to version 3.10 or higher.")

    # 2. GTK4 and GtkSourceView 5 check
    gtk_ok, gtk_msg, gtk_hints = check_pygobject_and_gtk()
    status_gtk = "[ PASS ]" if gtk_ok else "[ FAIL ]"
    print(f"{status_gtk} GTK & SourceView: {gtk_msg}")
    if not gtk_ok:
        all_passed = False
        action_items.extend(gtk_hints)

    # 3. ydotool check
    ydo_ok, ydo_msg, ydo_hints = check_ydotool()
    status_ydo = "[ PASS ]" if ydo_ok else "[ FAIL ]"
    print(f"{status_ydo} ydotool Backend: {ydo_msg}")
    if not ydo_ok:
        all_passed = False
        action_items.extend(ydo_hints)

    print("-" * 60)
    if all_passed:
        print("Result: ALL PREREQUISITES MET. Environment is ready for CodeTyper.")
        print("=" * 60)
        return 0
    else:
        print("Result: MISSING PREREQUISITES DETECTED.")
        print("\nActionable steps:")
        for idx, item in enumerate(action_items, 1):
            print(f"  {idx}. {item}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
