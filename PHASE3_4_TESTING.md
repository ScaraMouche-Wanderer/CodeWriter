# Phase 3 & 4 Testing Guide — Text Processor, Countdown Overlay & State Machine

This document outlines testing and verification steps for Phase 3 (Text Processor) and Phase 4 (Countdown Overlay & App State).

---

### Test 1: Unit Tests for Text Processor (Phase 3)

Run pytest on the test suite:
```bash
pytest tests/
```
**Verify**:
- All 6 tests pass without error.
- Tests verify nested C++ class indentation removal in Smart mode, exact match in Preserve mode, blank line preservation, mixed tabs/spaces, and edge cases.

---

### Test 2: Smart Mode End-to-End Typing (Phase 4)

1. Launch the application:
   ```bash
   python3 app.py
   ```
2. Paste the following nested snippet into the editor:
   ```cpp
   class Solution {
   public:
       int solve(int n) {
           return n * 2;
       }
   };
   ```
3. Ensure **Mode: Smart** is selected.
4. Set **Countdown** to **3 sec** and **Delay** to **5 ms**.
5. Click **ARM & TYPE**.
6. **Verify**:
   - The dark translucent countdown overlay appears immediately with large centered numbers (`3`, `2`, `1`) and subtitle `"Focus target now"`.
   - The ARM & TYPE button and editor inputs are disabled during countdown.
   - Status bar updates in sync (`Starting in 3...`, `Starting in 2...`, etc.).
   - Click into a target editor before countdown hits 0.
   - After typing finishes, every line in the target editor has **0 leading indentation**, allowing the target editor's auto-formatter to format it cleanly.
   - Overlay disappears and UI re-enables.

---

### Test 3: Preserve Mode End-to-End Typing

1. In CodeTyper, switch **Mode** to **Preserve**.
2. Click **ARM & TYPE** and focus your target editor.
3. **Verify**:
   - The typed output in the target editor preserves the original leading indentation verbatim.

---

### Test 4: Countdown Cancellation

1. Set **Countdown** to **5 sec**.
2. Click **ARM & TYPE**.
3. While the overlay is counting down, click the **Cancel** button on the overlay.
4. **Verify**:
   - Countdown stops immediately.
   - The overlay disappears.
   - Nothing is typed into the target window.
   - Status bar displays: `Status: Cancelled.`
   - All controls return to interactive/enabled state.

---

### Test 5: Instant Typing (0-Second Countdown)

1. Set **Countdown** spin button to **0 sec**.
2. Click **ARM & TYPE**.
3. **Verify**:
   - Typing executes immediately without flashing the overlay.
   - Status bar shows `Status: Typed N characters.`
   - Controls are cleanly restored to enabled state.

---

### Test 6: Button Sensitivity & State Safety

1. During an active countdown, verify that the ARM & TYPE button is not clickable (disabled), preventing double-triggering.
2. Verify that upon completion, cancellation, or error, the UI controls (ARM button, SpinButtons, Radio buttons, Editor) are all re-enabled.
