# Phase 9, 10, and 11 Testing Guide — CodeTyper v1 Complete

This document outlines manual and automated testing procedures for:
- **Phase 9**: Recent Snippets (10-item cap, deduplication, reload confirmation).
- **Phase 10**: Settings Persistence (window dimensions, last-selected profile).
- **Phase 11**: Polish & Packaging (Desktop install, keyboard navigation, Escape handling, exception boundary).

---

## Part A — Phase 9: Recent Snippets

### Test 1: Typing Multiple Snippets & Ordering
1. Launch CodeTyper:
   ```bash
   python3 app.py
   ```
2. Type 3 distinct snippets through complete ARM & TYPE cycles:
   - Snippet 1: `def hello(): return 1`
   - Snippet 2: `class Solution: pass`
   - Snippet 3: `int main() { return 0; }`
3. Expand the **Recent Snippets** panel.
4. **Verify**:
   - All 3 snippets appear in the list.
   - Snippet 3 is at the top (most recent first).

### Test 2: Deduplication & Move-to-Top
1. In the editor, paste the exact content of Snippet 1 (`def hello(): return 1`).
2. Click **ARM & TYPE**.
3. **Verify**:
   - Total snippet count remains 3.
   - Snippet 1 moves to the top of the list with an updated timestamp.

### Test 3: 10-Item Cap
1. Type 9 more distinct snippets (total 12 distinct typing runs).
2. **Verify**:
   - The Recent list displays exactly 10 items (`Recent Snippets (10)`).
   - The two oldest snippets have been dropped.

### Test 4: Reloading Snippets into Editor & Safe Replace Confirmation
1. With text in the editor, click any row in the Recent Snippets list.
2. **Verify**:
   - A confirmation dialog appears: *"Replace Editor Content?"*.
   - Clicking **Cancel** leaves the editor text untouched.
   - Clicking **Replace** loads the selected snippet into the editor.
3. Clear the editor completely and click a Recent snippet.
4. **Verify**: The snippet loads immediately without prompting.

---

## Part B — Phase 10: Settings Persistence

### Test 5: Window Size Persistence
1. Resize the CodeTyper window to a custom size (e.g. 950x700).
2. Close the application.
3. Relaunch:
   ```bash
   python3 app.py
   ```
4. **Verify**: The window restores and opens at 950x700.

### Test 6: Last-Selected Profile Persistence
1. Select a non-Default profile (e.g. `GFG C++`).
2. Close CodeTyper.
3. Relaunch `python3 app.py`.
4. **Verify**: `GFG C++` is automatically pre-selected in the profile dropdown.

### Test 7: Settings Self-Healing on Corrupt File
1. Corrupt `~/.local/share/codetyper/settings.json`:
   ```bash
   echo "{corrupt json..." > ~/.local/share/codetyper/settings.json
   ```
2. Relaunch `python3 app.py`.
3. **Verify**: Application launches cleanly with default 700x600 dimensions and Default profile.

---

## Part C — Phase 11: Polish & Packaging

### Test 8: Desktop Installation
1. Run the install script:
   ```bash
   ./scripts/install.sh
   ```
2. **Verify**:
   - Desktop entry is installed to `~/.local/share/applications/codetyper.desktop`.
   - SVG icon is copied to `~/.local/share/icons/hicolor/scalable/apps/codetyper.svg`.
   - CodeTyper appears in your GNOME App Grid and can be launched without a terminal.

### Test 9: Keyboard Navigation & Enter Handling
1. Focus the **Delay** or **Countdown** spin buttons using `Tab`.
2. Press `Enter`.
3. **Verify**: The numeric value is accepted and ARM & TYPE is **NOT** accidentally triggered.

### Test 10: Escape Key Abort (Focused Window)
1. Set countdown to 5 seconds.
2. Click **ARM & TYPE**.
3. During the countdown, press `Escape`.
4. **Verify**: The countdown immediately aborts and returns the app to `IDLE` state.

---

## Part D — Complete Automated Test Suite

Run the full pytest suite:
```bash
pytest tests/
```
**Verify**:
- All 23 tests across `test_text_processor.py`, `test_typing_engine.py`, `test_profiles.py`, `test_snippets.py`, and `test_settings.py` pass.
