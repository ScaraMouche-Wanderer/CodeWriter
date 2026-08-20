<div align="center">

<img src="resources/icons/codewriter.svg" width="96" height="96" alt="CodeWriter Logo" />

# CodeWriter

### *Hardware-level keystroke streamer & code typing engine for Linux.*

[![Platform](https://img.shields.io/badge/Platform-Linux%20(Wayland%20%7C%20X11)-1d1d1f?style=flat-square&logo=linux&logoColor=white)](https://github.com/ScaraMouche-Wanderer/CodeWriter)
[![GUI](https://img.shields.io/badge/GUI-GTK4%20%2B%20GtkSourceView%205-0066cc?style=flat-square&logo=gnome&logoColor=white)](https://github.com/ScaraMouche-Wanderer/CodeWriter)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://github.com/ScaraMouche-Wanderer/CodeWriter)
[![Tests](https://img.shields.io/badge/Tests-98%20Passed-34c759?style=flat-square&logo=pytest&logoColor=white)](https://github.com/ScaraMouche-Wanderer/CodeWriter)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

<br/>

**Paste disabled? Remote VM? Locked web console? Interview environment?**<br/>
CodeWriter streams your code directly into any window as native hardware keystrokes via `ydotool`.

</div>

---

## ⚡ 30-Second Quickstart

```bash
# Clone & install
git clone https://github.com/ScaraMouche-Wanderer/CodeWriter.git
cd CodeWriter && ./scripts/install.sh

# Launch
python3 app.py
```

---

## 💡 How It Works

```text
 ┌────────────────┐      Ctrl+Enter      ┌─────────────────┐      3... 2... 1...     ┌───────────────────────┐
 │ 1. Stage Code  │ ───────────────────> │ 2. Arm & Switch │ ──────────────────────> │ 3. Hardware Streaming │
 │  Paste/Format  │                      │    Target Win   │                         │  Types at Your Cursor │
 └────────────────┘                      └─────────────────┘                         └───────────────────────┘
```

---

## ✨ Features at a Glance

| Feature | Description |
|---|---|
| **🎲 Stealth Humanizer** | Natural $\pm 25\%$ jitter, punctuation thought pauses, and realistic typo auto-correction. |
| **🎬 Live Visualizer** | Real-time animated simulation player (`Ctrl+Shift+P`) with `0.5x`–`10x` speeds and live WPM. |
| **🛠 Code Beautifier** | Auto-format JSON, SQL, HTML (`Ctrl+Shift+F`), Base64/URL encoding, and AI Markdown cleaner (`Ctrl+M`). |
| **📝 Multi-Tab Editor** | Syntax highlighting for **22 languages**, soft word wrap (`Alt+Z`), line moving, and font zoom (`Ctrl++`/`-`). |
| **🎛 System Tray & Audio** | Native DBus StatusNotifierItem tray menu with live status, acoustic countdown ticks, and completion chimes. |

---

## ⌨️ Essential Shortcuts

```text
 ⚡ Control                         🛠 Editing & Tools
 ────────────────────────────────   ───────────────────────────────────
  Ctrl + Enter   ARM & TYPE NOW      Ctrl + Shift + F  Auto-Format Code
  Space          Pause / Resume      Ctrl + M          Extract AI Code
  Escape         Stop / Cancel       Ctrl + Shift + D  Duplicate Line
  Ctrl + P       Dry Run Preview     Ctrl + Shift + K  Delete Line
  Ctrl + Shift+P Live Visualizer     Alt + Up / Down   Move Line Up / Down
  Ctrl + ,       Preferences         Alt + Z           Toggle Word Wrap
  Ctrl + 1/2/3   Speed (2/8/20ms)    Ctrl + + / - / 0  Zoom In / Out / Reset
```

---

## 📦 Requirements & Setup

```bash
# Ubuntu / Debian / Pop!_OS
sudo apt update && sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-gtksource-5 ydotool librsvg2-bin

# Arch Linux / Manjaro
sudo pacman -S --needed python-gobject gtk4 gtksourceview5 ydotool librsvg

# Fedora
sudo dnf install -y python3-gobject gtk4 gtksourceview5 ydotool librsvg2-tools
```

> **Note**: Start the keystroke daemon once:
> ```bash
> systemctl --user enable --now ydotool.service || sudo systemctl enable --now ydotool.service
> ```

---

## 🧪 Tests

```bash
python3 -m pytest tests/ -v
```
*98 tests passing across typing engine, formatters, humanizer, settings, and tray DBus interfaces.*

---

## 📄 License

MIT © [ScaraMouche-Wanderer](https://github.com/ScaraMouche-Wanderer)
