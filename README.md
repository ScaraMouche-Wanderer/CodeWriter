# CodeWriter ⚡

<p align="center">
  <img src="resources/icons/codewriter.svg" width="112" height="112" alt="CodeWriter Icon" />
</p>

<p align="center">
  <strong>The ultra-fast, native Linux code streaming, keystroke automation & code beautification utility.</strong><br>
  Engineered to bypass clipboard and paste restrictions on remote desktops, VM web consoles, online IDEs, and coding interview platforms via hardware-level <code>ydotool</code> simulation.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Linux%20(Wayland%20%7C%20X11)-0066cc?logo=linux&logoColor=white" alt="Platform" />
  <img src="https://img.shields.io/badge/GUI-GTK4%20%2B%20GtkSourceView%205-247BA0?logo=gnome&logoColor=white" alt="GTK4" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Tests-98%20Passed%20(100%25)-34c759?logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License" />
</p>

<p align="center">
  <a href="#-quick-start"><strong>⚡ Quick Start</strong></a> •
  <a href="#-key-features">Features</a> •
  <a href="#-keyboard-shortcuts">Shortcuts</a> •
  <a href="#-code-tools--beautifiers">Code Tools</a> •
  <a href="#-system-requirements--dependencies">Installation</a> •
  <a href="USER_GUIDE.md">User Guide</a> •
  <a href="#-license">License</a>
</p>

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ScaraMouche-Wanderer/CodeWriter.git
cd CodeWriter

# 2. Run the quick desktop installer (installs launcher & HD icon assets)
./scripts/install.sh

# 3. Launch CodeWriter
python3 app.py
```

---

## 🚀 Key Features

### ⚡ Human-Like Cadence & Stealth Keystroke Simulation
- **Interactive Pause & Resume (`Space` / `Ctrl+Shift+P`)**: Freeze and resume active typing streams mid-session without losing your place.
- **Natural Cadence Jitter (`🎲 Human`)**: Keystroke timings vary naturally ($\pm 25\%$) rather than firing at robotic fixed intervals, perfectly mimicking human typing.
- **Realistic Typo & Auto-Correction Engine**: Simulates authentic QWERTY typo slips, cognitive pause (80–180ms), backspace keystrokes, and re-typing the correction.
- **Syntax Thought Pauses**: Automatically introduces natural pauses on newlines ($40-100\text{ms}$) and punctuation delimiters (`{`, `}`, `;`, `:`).
- **Speed Presets**: Instant 1-click toggles for **Fast** (2ms), **Normal** (8ms), **Safe** (20ms), or custom microsecond precision ($1-1000\text{ms}$).

### 🎬 Live Simulation Player & Visualizer (`Ctrl+Shift+P`)
- **Animated Playback Canvas**: Preview the exact keystroke typing sequence on an interactive animated screen with live WPM meter and character progression counters.
- **Speed Multipliers**: `0.5x` (Slow), `1.0x` (Real-time), `2.0x` (Fast), `5.0x` (Blitz), `10.0x` (Instant).
- **Direct Trigger**: **`⚡ ARM & TYPE NOW`** button to launch actual keystroke transmission immediately from the visualizer.

### 🛠 Code Tools, Beautifiers & Encoders (`Ctrl+Shift+F`)
- **Auto-Format Code (`Ctrl+Shift+F`)**: Automatically detects the active programming language and applies the appropriate beautifier.
- **JSON Formatter & Minifier**: Pretty-prints formatted JSON with syntax validation or compresses into a single compact line.
- **SQL Query Beautifier**: Capitalizes SQL keywords (`SELECT`, `FROM`, `WHERE`, `JOIN`, `ORDER BY`, `LIMIT`) and formats clause indentations.
- **HTML / XML Formatter**: Rebuilds tag hierarchies with proper nesting and void tag handling.
- **Data Encoders**: Instant Base64 encode/decode and URL percent encode/decode.
- **AI Markdown Extractor (`Ctrl+M`)**: Automatically strips conversational text and ````code fences when pasting from ChatGPT, Claude, Gemini, or DeepSeek.
- **Clean & Stealth**: Language-aware removal of comments (`//`, `#`, `--`, `/* */`), docstrings, and IDE bracket auto-close compensation.

### ⚙️ Multi-Tab Editor & Comprehensive Preferences (`Ctrl+,`)
- **Multi-Tab Architecture**: Open up to 8 independent tabs with syntax highlighting across **22 languages**.
- **Font Zooming & Soft Wrap**: `Ctrl++` / `Ctrl+-` font scaling and `Alt+Z` soft word wrapping.
- **Line Manipulations**: `Alt+Up` / `Alt+Down` (Move lines), `Ctrl+Shift+D` (Duplicate line/selection), `Ctrl+Shift+K` (Delete line).
- **System Tray Integration**: Pure DBus StatusNotifierItem with live status, dynamic tooltips, and context menu.
- **Acoustic Feedback**: Audible countdown clicks and completion chime.

---

## ⌨️ Keyboard Shortcuts

| Category | Shortcut | Action |
|---|---|---|
| **Typing & Simulation** | `Ctrl+Enter` | **⚡ ARM & TYPE NOW** |
| | `Space` | **Pause / Resume Typing** (during active stream) |
| | `Escape` | **Stop / Cancel** typing countdown or stream |
| | `Ctrl+P` | **Pre-Flight Preview / Dry Run** |
| | `Ctrl+Shift+P` | **🎬 Live Simulation Player / Visualizer** |
| **Code Tools** | `Ctrl+Shift+F` | **Auto Format Code** (JSON / SQL / HTML) |
| | `Ctrl+M` | **Extract AI Markdown Code** |
| | `Ctrl+Shift+D` | **Duplicate Line / Selection** |
| | `Ctrl+Shift+K` | **Delete Current Line** |
| | `Alt+Up` / `Alt+Down` | **Move Current Line Up / Down** |
| | `Alt+Z` | **Toggle Soft Word Wrap** |
| | `Ctrl++` / `Ctrl+-` / `Ctrl+0` | **Zoom In / Zoom Out / Reset Font** |
| **Editor & File** | `Ctrl+F` / `Ctrl+H` | **Find** / **Find & Replace** |
| | `Ctrl+O` / `Ctrl+S` | **Open File** / **Save File** |
| | `Ctrl+L` | **Clear Editor** |
| **Application** | `Ctrl+,` | **⚙️ CodeWriter Preferences** |
| | `Ctrl+1` / `Ctrl+2` / `Ctrl+3` | **Fast (2ms)** / **Normal (8ms)** / **Safe (20ms)** |
| | `Ctrl+?` | **Show Shortcuts Cheat Sheet** |

---

## 📦 System Requirements & Dependencies

CodeWriter runs natively on **Linux (Wayland & X11)**:

```bash
# Debian / Ubuntu / Pop!_OS
sudo apt update && sudo apt install -y python3-gi gir1.2-gtk-4.0 gir1.2-gtksource-5 ydotool librsvg2-bin

# Fedora / RHEL
sudo dnf install -y python3-gobject gtk4 gtksourceview5 ydotool librsvg2-tools

# Arch Linux / Manjaro
sudo pacman -S --needed python-gobject gtk4 gtksourceview5 ydotool librsvg
```

Ensure `ydotoold` daemon is running:
```bash
systemctl --user enable --now ydotool.service || sudo systemctl enable --now ydotool.service
```

---

## 🧪 Testing

CodeWriter includes a 98-test automated suite covering the typing engine, humanizer cadence, formatters, tray DBus interfaces, and settings:

```bash
python3 -m pytest tests/ -v
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
