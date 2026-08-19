# Phase 5 & 6 Testing Guide — Background Typing Engine, Chunking & STOP Button

This document outlines manual and automated testing procedures for Phase 5 (Typing Engine & Chunking) and Phase 6 (STOP Button & Cancellation).

---

### Test 1: Unit Test Suite Verification (Pytest)

Run all unit tests:
```bash
pytest tests/
```
**Verify**:
- All 10 tests in `test_text_processor.py` and `test_typing_engine.py` pass.
- Tests verify chunk formula clamping (`calculate_chunk_size`), multi-chunk background execution, cancellation between chunks, and error propagation.

---

### Test 2: Background Responsiveness During Large Pastes (Phase 5)

1. Launch CodeTyper:
   ```bash
   python3 app.py
   ```
2. Paste a large code file (> 2,000 characters) into the editor.
3. Set **Delay** to **Normal (8ms)** and **Countdown** to **3 sec**.
4. Click **ARM & TYPE** and focus a target text editor.
5. **Verify**:
   - The CodeTyper window remains completely responsive during typing — you can move or resize the window without any freeze.
   - Status bar updates incrementally in chunk steps: `Typing... 50/2000 characters`, `Typing... 100/2000 characters`, etc.
   - On completion, status bar reads: `Status: Typed 2000 characters.`
   - No characters are dropped or repeated in the target window.

---

### Test 3: Preset Chunk Sizing (Fast vs Safe)

1. **Fast Preset (2ms)**:
   - Chunk size computes to **200 characters** (maximum ceiling).
   - Character count increments in large jumps (+200).
2. **Safe Preset (20ms)**:
   - Chunk size computes to **20 characters** (minimum floor).
   - Character count increments in smaller, steady jumps (+20).

---

### Test 4: STOP Button Cancellation (Phase 6)

1. **Cancellation During Countdown**:
   - Set Countdown to **5 sec**. Click **ARM & TYPE**.
   - Either click **Cancel** on the countdown overlay OR the red **STOP** button in the main window.
   - Verify countdown halts immediately, nothing is typed, and status shows: `Status: Cancelled.`

2. **Cancellation During Active Typing**:
   - Paste 2,000 characters. Set Delay to **Normal (8ms)** and Countdown to **1 sec**.
   - Click **ARM & TYPE**. Once typing begins, click the red **STOP** button.
   - Verify typing halts cleanly within ~1 chunk (~400ms).
   - Verify status label freezes displaying: `Status: Stopped at N characters.`
   - Verify ARM & TYPE button immediately re-appears and is enabled.
   - Verify typing can be started again immediately without leftover state or errors.

---

### Test 5: STOP Stress Test (10x Repetition)

1. Start 10 consecutive typing sessions on a large paste.
2. Click **STOP** at different stages (early, middle, near-end).
3. Verify that in all 10 trials:
   - No deadlocks, stuck states, or crashes occur.
   - Every cancellation returns the UI to `IDLE` state with enabled controls.

---

### Test 6: Error Handling Path

1. Run the app with an invalid backend to simulate runtime failure:
2. Verify that if backend raises an error, `_on_typing_error` catches it, sets status to `Status: Error: ...`, and restores state to `IDLE`.
