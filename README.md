# CodeTyper

**CodeTyper** is a native Linux desktop utility designed to bypass Wayland clipboard and paste restrictions on web apps, online code evaluation platforms, and virtual environments by simulating real, character-by-character hardware keystrokes using `ydotool`.

---

## Key Features

- **GtkSourceView Editor**: Monospace code editor with line numbering and syntax preparation.
- **Smart Indentation Mode**: Automatically strips per-line leading whitespace while preserving blank lines and relative block nesting to work harmoniously with online auto-indenting editors.
- **Preserve Mode**: Transmits raw text exactly as pasted with all whitespace and formatting intact.
- **Configurable Typing Speed & Delay**: Fine-grained delay controls (presets for Fast 2ms, Normal 8ms, Safe 20ms, and custom 0–200ms).
- **Visual Countdown Overlay**: Customizable countdown (0–10s) with fullscreen visual cues to give you time to focus your target window.
- **Background Typing Engine**: Non-blocking background worker that streams code in adaptive chunks (~400ms batches) without locking the UI.
- **Progress Bar & STOP Control**: Real-time progress percentage bar and dedicated STOP button with inter-chunk cancellation.
- **Persistent Profiles**: Save named configuration presets (e.g. "Default", "GFG C++", "LeetCode Python") to `~/.local/share/codetyper/profiles.json`.
- **Recent Snippets History**: Automatically tracks the last 10 typed snippets in a collapsible history panel with 1-click reload and replacement safeguards.
- **Settings Persistence**: Remembers window dimensions and your last-selected profile across restarts.

---

## Requirements & Dependencies

CodeTyper is built for **Linux on Wayland / X11** with GNOME or other desktop environments:

- **Python**: `>= 3.10`
- **PyGObject & GTK4**: `libgtk-4-dev` / `gtk4`
- **GtkSourceView 5**: `libgtksourceview-5-dev` / `gtksourceview5`
- **ydotool & ydotoold**: `ydotool` daemon running in user or system session.

### Environment Validation
Run the built-in diagnostic tool to verify all system dependencies:
```bash
python3 scripts/check_env.py
```

To start the `ydotoold` background daemon if not already active:
```bash
ydotoold &
```

---

## Installation & Running

### Run Directly
```bash
python3 app.py
```

### Install to Desktop Application Grid
Install the desktop launcher and icon into `~/.local/share/applications/` and `~/.local/share/icons/`:
```bash
./scripts/install.sh
```
Once installed, **CodeTyper** will appear directly in your GNOME App Grid and application launcher.

---

## Known Wayland Limitations

- **Escape Key Abort**: Pressing the `Escape` key will abort countdowns and stop typing **only while CodeTyper retains window focus** (e.g., during the initial countdown before switching windows).
- Under Wayland security architecture, compositors do not forward global keystrokes to unfocused background windows. Once focus has shifted to your target editor window during typing, use the visible red **STOP** button to safely halt typing.
