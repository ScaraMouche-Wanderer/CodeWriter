# Phase 7 & 8 Testing Guide — Progress Bar & Profile Persistence

This document outlines testing and verification procedures for Phase 7 (Progress Bar) and Phase 8 (Profile Persistence).

---

## Part A — Phase 7: Progress Bar

### Test 1: Progress Bar Appearance and Incremental Filling
1. Launch the application:
   ```bash
   python3 app.py
   ```
2. Paste a long code snippet (> 1,000 characters) into the editor.
3. Set **Countdown** to **3 sec** and **Delay** to **Normal (8ms)**.
4. Click **ARM & TYPE**.
5. **Verify**:
   - The progress bar appears immediately when countdown begins, initialized at **0%** (`0 / 0 characters`).
   - Once typing begins, the progress bar smoothly fills in chunks, with its overlay text displaying: `X / Total characters`.
   - The progress text and bar visually sync with the status label text below it.

### Test 2: Completion State
1. Allow the typing session to complete fully.
2. **Verify**:
   - The progress bar shows **100%** on completion.
   - Upon state transitioning back to `IDLE`, the progress bar cleanly hides and the ARM & TYPE button re-appears.

### Test 3: Cancellation Freezes Progress Bar
1. Start another long typing session.
2. Partway through typing, click the red **STOP** button.
3. **Verify**:
   - The progress bar freezes at the exact stopped percentage and does NOT reset to 0%.
   - The progress bar value matches the status label message: `Status: Stopped at N characters.`

### Test 4: Reset on Next Run
1. Immediately after a cancelled run, click **ARM & TYPE** again.
2. **Verify**:
   - The progress bar immediately resets to **0%** at countdown start, clearing any remnant percentage from the previous run.

---

## Part B — Phase 8: Profile Persistence

### Test 5: Fresh Run & Self-Healing Default Profile
1. Remove any existing test profiles:
   ```bash
   rm -f ~/.local/share/codetyper/profiles.json
   ```
2. Launch the application:
   ```bash
   python3 app.py
   ```
3. **Verify**:
   - The Profile dropdown displays `Default`.
   - Delay is set to **5 ms**, Countdown to **3 sec**, and Mode to **Smart**.
   - `~/.local/share/codetyper/profiles.json` was automatically created on disk.

### Test 6: Creating and Saving a New Profile
1. In CodeTyper, adjust settings:
   - Set **Delay** to **15 ms**.
   - Set **Countdown** to **5 sec**.
   - Set **Mode** to **Preserve**.
2. Click **Save as Profile**.
3. In the popup dialog, enter `GFG C++` and click **Save**.
4. **Verify**:
   - The dialog closes.
   - The Profile dropdown now displays `GFG C++` as the active selected profile.

### Test 7: Switching Profiles in Real-Time
1. Open the Profile dropdown and select `Default`.
2. **Verify**: Controls immediately revert to `5 ms`, `3 sec`, and `Smart`.
3. Open the Profile dropdown and select `GFG C++`.
4. **Verify**: Controls immediately update to `15 ms`, `5 sec`, and `Preserve`.

### Test 8: App Restart & Disk Persistence
1. Close CodeTyper completely.
2. Relaunch:
   ```bash
   python3 app.py
   ```
3. **Verify**:
   - Both `Default` and `GFG C++` appear in the dropdown.
   - Selecting `GFG C++` restores all saved parameters accurately from disk.

### Test 9: Corrupt File Self-Healing
1. Manually corrupt the JSON file:
   ```bash
   echo "{broken json" > ~/.local/share/codetyper/profiles.json
   ```
2. Relaunch `python3 app.py`.
3. **Verify**:
   - The application does not crash.
   - The dropdown gracefully falls back to `Default`.
   - The file on disk is self-healed and rewritten with valid default JSON.

---

## Part C — Automated Test Suite

Run all unit tests:
```bash
pytest tests/
```
**Verify**:
- All 14 tests across `test_text_processor.py`, `test_typing_engine.py`, and `test_profiles.py` pass.
