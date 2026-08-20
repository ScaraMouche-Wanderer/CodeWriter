# CodeWriter — Complete In-Depth User Manual & Guide

Welcome to the **CodeWriter** user guide. This document provides a comprehensive, step-by-step walkthrough of every command, option, keyboard shortcut, and workflow feature available in CodeWriter.

---

## Table of Contents

1. [Quick Start (3-Step Workflow)](#1-quick-start-3-step-workflow)
2. [Interface Layout Overview](#2-interface-layout-overview)
3. [Text Processing Modes (Smart, Preserve, Strip Lines)](#3-text-processing-modes)
4. [Timing, Speed Presets & Human Cadence](#4-timing-speed-presets--human-cadence)
5. [Stealth Typo & Self-Correction Engine](#5-stealth-typo--self-correction-engine)
6. [AI Code Cleaning & Code Tools (`Tools` Menu)](#6-ai-code-cleaning--code-tools-tools-menu)
7. [Starter Boilerplates (`Templates` Menu)](#7-starter-boilerplates-templates-menu)
8. [Multi-Tab Editor & Selection Scope Typing](#8-multi-tab-editor--selection-scope-typing)
9. [Profiles, History & Session Analytics](#9-profiles-history--session-analytics)
10. [Complete Keyboard Shortcuts Reference](#10-complete-keyboard-shortcuts-reference)
11. [Terminal Commands & Scripts](#11-terminal-commands--scripts)
12. [Troubleshooting & FAQs](#12-troubleshooting--faqs)
13. [Supported Languages & Syntax Highlighting](#13-supported-languages--syntax-highlighting)
14. [Find & Replace In-Editor Search](#14-find--replace-in-editor-search)
15. [Drag-and-Drop File Loading](#15-drag-and-drop-file-loading)
16. [Data Storage & JSON File Formats](#16-data-storage--json-file-formats)
17. [Desktop Notifications](#17-desktop-notifications)
18. [Emergency Stop & Safety Guarantee](#18-emergency-stop--safety-guarantee)


---

## 1. Quick Start (3-Step Workflow)

CodeWriter streams code directly into any focused window using hardware keystroke simulation (bypassing clipboard blocks on remote desktops, VM consoles, and online interview portals).

```
┌───────────────────────────┐      ┌───────────────────────────┐      ┌───────────────────────────┐
│ 1. Paste / Write Code     │ ───> │ 2. Press ARM & TYPE       │ ───> │ 3. Click Target Window    │
│    (or drag-and-drop file)│      │    (or hit Ctrl+Enter)    │      │    (CodeWriter streams it)│
└───────────────────────────┘      └───────────────────────────┘      └───────────────────────────┘
```

1. **Input Your Code**: Paste or type code into the CodeWriter editor buffer (or drag & drop a file).
2. **Arm the Stream**: Click **ARM & TYPE** or press `Ctrl + Enter`.
3. **Switch to Target Window**: During the countdown (e.g. 3 seconds), click into the target text editor, VM console, or web browser. When countdown ends, CodeWriter automatically types the code.

---

## 2. Interface Layout Overview

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ Profile: [ Default  ▼ ] [ 💾 Save ] [ 🗑️ Delete ]         [ ⏳ History ] [ 📊 Logs ] [ ⌨ ]│ <-- Top App Bar
├──────────────────────────────────────────────────────────────────────────────────┤
│ Lang: [ Python ▼ ] [ ⚙️ Tools ▼ ] [ 📄 Templates ▼ ]    [ 📂 Open ] [ 💾 Save ] [ 📋 ] [ ✕ ]│ <-- Editor Toolbar
├──────────────────────────────────────────────────────────────────────────────────┤
│ [ Untitled ✕ ] [ solution.py ✕ ] [ + ]                                          │ <-- Tab Bar
├──────────────────────────────────────────────────────────────────────────────────┤
│ 1  def solve(grid: list[list[int]]) -> int:                                     │
│ 2      # Code editor canvas with syntax highlighting                             │
│ 3      return sum(sum(row) for row in grid)                                     │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Mode: (•) Smart   ( ) Preserve   ( ) Strip Lines                     Wait: [ 3 ] s│ <-- Control Deck (Row 1)
│ Speed: [ Fast (2ms) ] [ Normal (8ms) ] [ Safe (20ms) ] [ ⭐ Human ]   Delay: [ 5 ] ms│ <-- Control Deck (Row 2)
├──────────────────────────────────────────────────────────────────────────────────┤
│ [                       ▶ ARM & TYPE (Ctrl+Enter)                               ]│ <-- Action Row
├──────────────────────────────────────────────────────────────────────────────────┤
│ Status: Ready                                                 3 lines · 98 chars │ <-- Status Footer
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Text Processing Modes

Located on the bottom control deck. Choose how whitespace and line formatting are handled before transmission:

### 🔹 `Smart` Mode (Default — Recommended)
- **What it does**: Automatically removes leading indentation spaces/tabs from the start of every line while keeping internal spacing intact.
- **When to use**: Use when typing into code editors that have **auto-indentation** enabled (e.g., VS Code, LeetCode, HackerRank, Sublime, IntelliJ). 
- **Why it matters**: Prevents the *"staircase indentation bug"* where automatic editor indentation stacks on top of your pasted spaces, ruining Python or C++ indentation.

### 🔹 `Preserve` Mode
- **What it does**: Leaves the text 100% untouched and transmits every single space, tab, and newline verbatim.
- **When to use**: Use when typing into plain terminals, `cat > file.txt`, raw `nano`, web forms without auto-indent, or multi-line raw string payloads.

### 🔹 `Strip Lines` Mode
- **What it does**: Automatically detects and strips leading line numbers from copied code blocks.
- **Supported Formats**:
  - `1: def foo():` $\rightarrow$ `def foo():`
  - `01. int main() {` $\rightarrow$ `int main() {`
  - `1 | print("hello")` $\rightarrow$ `print("hello")`
- **When to use**: When copying snippets directly from code review tools, IDE line gutters, or tutorials where line numbers were accidentally included.

---

## 4. Timing, Speed Presets & Human Cadence

### ⏱️ Wait (Countdown Spinner)
- **Setting**: `0` to `10` seconds (Default: `3s`).
- **Purpose**: Gives you sufficient time after clicking **ARM & TYPE** to switch focus (Alt+Tab or mouse click) to your target window before keystrokes start emitting.

### ⚡ Speed Presets
| Preset | Delay per Char | Effective Speed | Best Used For |
|---|---|---|---|
| **Fast** | `2 ms` | ~400+ WPM | Large codebases, fast local VMs, responsive editors |
| **Normal** | `8 ms` | ~150 WPM | Standard web IDEs (LeetCode, HackerRank, Codility) |
| **Safe** | `20 ms` | ~60 WPM | Slow remote desktops, VNC, RDP, high-latency SSH web consoles |
| **Custom** | `0 – 200 ms` | Micro-adjustable | Fine-tuned custom millisecond rate |

### ⭐ Human Cadence (`Human` Toggle Button)
- **What it does**:
  1. **Timing Jitter**: Introduces subtle $\pm 25\%$ microsecond variation to each character delay instead of robotic fixed timing.
  2. **Newline Thought Pause**: Pauses $40\text{–}100\text{ms}$ after hitting Enter (simulating a human looking at the next line).
  3. **Delimiter Pause**: Pauses $15\text{–}35\text{ms}$ after structural punctuation (`;`, `{`, `}`, `:`).
- **When to use**: Anti-bot evasion and proctoring bypass on platforms that analyze keystroke intervals.

---

## 5. Stealth Typo & Self-Correction Engine

Located inside the **`Tools`** popover under **Typo Simulation Rate**:

### Options:
- **Off (0%)**: Perfect typing without intentional mistakes.
- **Subtle (1%)**: ~1 typo every 100 characters.
- **Realistic (3%)**: ~3 typos every 100 characters.

### How the Engine Works:
```
1. Target char 'a' ──> 2. Types neighbor 's' ──> 3. Cognitive pause (80-180ms) ──> 4. Hardware Backspace ──> 5. Types 'a'
```
- Uses a physical **QWERTY keyboard neighbor matrix** so typos are natural (e.g. typing `s` or `q` instead of `a`).
- Pauses for a realistic human reaction window ($80\text{–}180\text{ms}$).
- Sends physical hardware backspace keycode (`14`) via `ydotool` to erase the mistake and types the correct letter.

---

## 6. AI Code Cleaning & Code Tools (`Tools` Menu)

Click the **Tools** button in the toolbar to access instant code transformations:

| Tool / Option | Shortcut | What It Does |
|---|---|---|
| **Extract AI Code** | `Ctrl + M` | Automatically strips conversational text (e.g. *"Sure! Here is the solution:"*) and ````python ... ```` fences from ChatGPT / Claude / Gemini answers. |
| **Strip Comments & Docstrings** | — | Language-aware removal of `#`, `//`, `/* */`, `--` comments and Python `"""..."""` docstrings while preserving string literals. |
| **Compensate Auto-Close Brackets** | — | Replaces empty bracket pairs (`()`, `[]`, `{}`) with opening brackets (`(`, `[`, `{`) so auto-closing web editors don't generate duplicate closing brackets (`())`). |
| **Convert Tabs $\rightarrow$ Spaces** | — | Replaces all tab indentation with 4 spaces. |
| **Convert Spaces $\rightarrow$ Tabs** | — | Replaces 4-space indentations with tabs. |
| **Trim Trailing Whitespace** | — | Cleans invisible spaces and tabs at the ends of lines. |
| **Remove Blank Lines** | — | Collapses and strips empty/blank lines. |
| **Deduplicate Lines** | — | Removes duplicate lines while preserving line order. |
| **Sort Lines (A $\rightarrow$ Z)** | — | Alphabetically sorts lines in the editor. |
| **Change Case** | — | Converts selected identifiers to `camelCase`, `snake_case`, `kebab-case`, `PascalCase`, `UPPERCASE`, or `lowercase`. |
| **Pre-Flight Dry Run** | `Ctrl + P` | Displays estimated typing duration, word count, total characters, and effective WPM before arming. |

---

## 7. Starter Boilerplates (`Templates` Menu)

Click the **Templates** button in the toolbar for 1-click competitive programming & standard skeletons:

- **Python**: LeetCode Solution class, Fast I/O Template (`sys.stdin.readline`).
- **C++**: Competitive Fast I/O (`ios_base::sync_with_stdio(false)`), Standard `main()` skeleton.
- **Java**: Fast `BufferedReader` Solution class.
- **Rust**: Fast `io::stdin().read_to_string()` setup.
- **Go**: `bufio.Scanner` Fast I/O skeleton.
- **TypeScript / C / SQL**: Standard clean starter templates.

---

## 8. Multi-Tab Editor & Selection Scope Typing

### 📑 Tab Management
- Work with up to **8 independent editor tabs** simultaneously.
- Click `+` to open a new tab, or click `✕` to close a tab.
- Tabs automatically derive their names from the loaded file name or the first line of code.

### 🎯 Selection-Aware Scope Typing
- If you highlight/select a portion of code with your mouse or keyboard:
  - The ARM button automatically updates to: **`ARM & TYPE Selection (X chars)`**.
  - CodeWriter will **only transmit the selected lines**, leaving the rest untouched.
- If no text is selected, CodeWriter transmits the entire buffer.

---

## 9. Profiles, History & Session Analytics

### 💾 Profiles
- **Create a Profile**: Set your desired language, mode, speed, and countdown, click **Save**, and enter a profile name (e.g. *"LeetCode Python"* or *"Remote VM"*).
- **Switch Profiles**: Select from the **Profile** dropdown to restore all saved parameters instantly.
- **Delete Profile**: Select a custom profile and click **Delete** (the `Default` profile cannot be deleted).

### ⏳ Snippet History
- Click **History** to view your 10 most recent snippets.
- Click any row to reload that snippet into the editor.
- Includes a **Clear History** button to wipe cached snippets.

### 📊 Session Analytics
- Click **Logs** to view all historical typing sessions with:
  - Timestamp, Character Count, Duration, Effective WPM, and Status (`complete`, `cancelled`, `error`).
  - All-time statistics summary (Total characters typed, total sessions, all-time average WPM).
- **Export to CSV**: Click **Export to CSV** to save session logs for reporting.

---

## 10. Complete Keyboard Shortcuts Reference

| Shortcut | Description | Context |
|---|---|---|
| **`Ctrl + Enter`** | **ARM & TYPE** | Starts countdown to begin typing |
| **`Space`** | **Pause / Resume** | Freezes/resumes active keystroke stream |
| **`Ctrl + Shift + P`** | **Pause / Resume** | Global toggle for active keystroke stream |
| **`Escape`** | **Stop / Cancel** | Immediately halts countdown or active stream; closes Find bar |
| **`Ctrl + P`** | **Dry-Run Preview** | Opens pre-flight estimation dialog |
| **`Ctrl + M`** | **Extract AI Markdown** | Extracts pure code from AI responses |
| **`Ctrl + O`** | **Open File** | Opens system file chooser |
| **`Ctrl + S`** | **Save File** | Saves current editor buffer to file |
| **`Ctrl + F`** | **Find** | Opens in-editor search bar |
| **`Ctrl + H`** | **Find & Replace** | Opens search and replace bar |
| **`Ctrl + L`** | **Clear Editor** | Clears the current buffer with confirmation |
| **`Ctrl + 1`** | **Fast Speed** | Sets delay to 2ms |
| **`Ctrl + 2`** | **Normal Speed** | Sets delay to 8ms |
| **`Ctrl + 3`** | **Safe Speed** | Sets delay to 20ms |
| **`Ctrl + ?`** | **Shortcuts Window** | Opens the interactive shortcut cheatsheet |

---

## 11. Terminal Commands & Scripts

### 🚀 Running the App
```bash
# Direct execution
python3 app.py

# Or using Makefile
make run

# Or via installed command
codewriter
```

### 🛠️ Environment & Hardware Diagnostics
```bash
# Check Python, GTK4, GtkSourceView 5, and ydotool reachability
python3 scripts/check_env.py
# (or make check-env)

# Send a 3-second diagnostic test typing payload
python3 scripts/test_ydotool.py
```

### 📦 System Installation
```bash
# Install desktop launcher and icons to ~/.local/share/
./scripts/install.sh
# (or make install)
```

### 🧪 Automated Tests
```bash
# Run full pytest test suite
pytest -v
# (or make test)
```

---

## 12. Troubleshooting & FAQs

### Q1: `ydotoold daemon unreachable` on startup
**Cause**: The hardware keystroke daemon `ydotoold` is not running or the socket is inaccessible.
**Solution**:
1. Start the daemon in the background:
   ```bash
   ydotoold &
   ```
   Or via systemd (if configured):
   ```bash
   systemctl --user start ydotoold
   ```
2. Ensure your user belongs to the `input` group:
   ```bash
   sudo usermod -aG input $USER
   ```
   *(Log out and log back in for group changes to take effect).*

---

### Q2: Code indentation looks duplicated / stepped (staircase bug)
**Cause**: Your target editor has auto-indentation enabled, and CodeWriter is typing extra leading spaces.
**Solution**: Set **Mode** to **`Smart`** on the bottom deck. `Smart` mode strips leading spaces so your target editor's auto-indentation produces clean alignment.

---

### Q3: Duplicate closing brackets like `def solve()):` or `arr = []]`
**Cause**: Target web editor (LeetCode / Monaco) automatically inserts closing brackets when opening brackets are typed.
**Solution**: Click **Tools** $\rightarrow$ **Compensate Auto-Close Brackets** before arming.

---

### Q4: How do I pause if a popup appears on my remote VM?
**Solution**: Hit **`Space`** or **`Ctrl + Shift + P`** or click the **PAUSE** button. Dismiss the popup in your target window, then hit **`Space`** or **RESUME** to continue exactly from the current character.

---

## 13. Supported Languages & Syntax Highlighting


CodeWriter includes built-in GtkSourceView 5 syntax highlighting for **22 programming languages and file formats**. Highlighting is automatically detected when loading or dropping files:

| Language | Language ID | Supported File Extensions |
|---|---|---|
| **Python** | `python` | `.py`, `.pyw` |
| **C** | `c` | `.c`, `.h` |
| **C++** | `cpp` | `.cpp`, `.cxx`, `.cc`, `.hpp`, `.hxx` |
| **Rust** | `rust` | `.rs` |
| **Go** | `go` | `.go` |
| **Java** | `java` | `.java` |
| **JavaScript** | `javascript` | `.js`, `.mjs`, `.cjs`, `.jsx` |
| **TypeScript** | `typescript` | `.ts`, `.tsx` |
| **Bash / Shell** | `sh` | `.sh`, `.bash`, `.zsh` |
| **JSON** | `json` | `.json` |
| **YAML** | `yaml` | `.yaml`, `.yml` |
| **TOML** | `toml` | `.toml` |
| **Markdown** | `markdown` | `.md`, `.markdown` |
| **HTML** | `html` | `.html`, `.htm` |
| **CSS** | `css` | `.css`, `.scss` |
| **SQL** | `sql` | `.sql` |
| **Ruby** | `ruby` | `.rb` |
| **PHP** | `php` | `.php` |
| **Kotlin** | `kotlin` | `.kt`, `.kts` |
| **Swift** | `swift` | `.swift` |
| **Lua** | `lua` | `.lua` |
| **Plain Text** | `plain` | `.txt`, (unrecognized extensions) |

---

## 14. Find & Replace In-Editor Search

Access the integrated in-editor search bar at any time:

### Controls & Actions:
- **`Ctrl + F`**: Opens the **Find** bar.
- **`Ctrl + H`**: Opens the **Find & Replace** bar.
- **`Enter`**: Finds and jumps to the next match.
- **`Shift + Enter`**: Jumps to the previous match.
- **`Aa` Button**: Toggles **Case-Sensitive** matching.
- **`Replace`**: Replaces the currently highlighted match.
- **`Replace All`**: Replaces every occurrence throughout the buffer.
- **`Escape`**: Closes the search bar and returns focus to the code canvas.

---

## 15. Drag-and-Drop File Loading

- **How to use**: Drag any source file from your file manager (Nautilus, Dolphin, Thunar, etc.) directly into the CodeWriter editor canvas.
- **Automatic Handling**:
  1. CodeWriter reads the file content with UTF-8 encoding.
  2. Detects the language syntax from the file extension.
  3. Updates the active tab title to the file name.
  4. Displays a confirmation status: `Loaded: filename.ext`.

---

## 16. Data Storage & JSON File Formats

All application data is stored in standard JSON files under `~/.local/share/codewriter/`:

### 1. `settings.json` (`~/.local/share/codewriter/settings.json`)
Stores window geometry and user preferences:
```json
{
  "window_width": 780,
  "window_height": 580,
  "last_selected_profile": "Default",
  "notify_on_complete": true,
  "humanize_cadence": false,
  "typo_rate": 0,
  "auto_close_compensate": false
}
```

### 2. `profiles.json` (`~/.local/share/codewriter/profiles.json`)
Stores named configuration presets:
```json
[
  {
    "name": "LeetCode Python",
    "language": "python",
    "mode": "smart",
    "delay_ms": 5,
    "countdown_sec": 3
  }
]
```

### 3. `snippets.json` (`~/.local/share/codewriter/snippets.json`)
Stores the 10 most recent snippets with derived titles and timestamps.

### 4. `sessions.json` (`~/.local/share/codewriter/sessions.json`)
Stores session logs (character count, duration in ms, calculated WPM, status).

---

## 17. Desktop Notifications

- When keystroke streaming completes, CodeWriter delivers a native Linux desktop notification (via `libnotify` / `Gio.Notification`):
  - **Success Notification**: `✓ Typed 482 chars in 2.4s (180 WPM)`
  - **Error Notification**: `✗ Typing error: [reason]`
- Can be toggled on/off in settings.

---

## 18. Emergency Stop & Safety Guarantee

- **Instant Abort**: Pressing **`Escape`** or clicking **`STOP`** cancels transmission within $\le 40\text{ms}$.
- **Buffer Safety**: Stopping or pausing never alters or deletes your editor buffer content.
- **Daemon Protection**: Automatic retry recovery and socket health checking prevent hanging if the background daemon is temporarily busy.

