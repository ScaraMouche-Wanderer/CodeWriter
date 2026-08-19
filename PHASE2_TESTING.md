# Phase 2 Testing Guide — ydotool Backend & Health Check

This document describes how to manually test and verify the Phase 2 implementation of CodeTyper.

---

### Test 1: Daemon Not Running (Health Check Dialog)

1. **Stop `ydotoold`**:
   ```bash
   killall ydotoold
   ```
2. **Launch the application**:
   ```bash
   python3 app.py
   ```
3. **Verify**:
   - The main window does NOT appear.
   - An error dialog appears titled **CodeTyper — Backend Unavailable**.
   - The message clearly states:
     `ydotoold is not running or socket is inaccessible. Start it with: ydotoold &`

---

### Test 2: Retry While Daemon is Stopped

1. With the error dialog open from Test 1, click **Retry**.
2. **Verify**:
   - The dialog remains open.
   - The error message updates in place with the same actionable daemon error.
   - The app does not crash or freeze.

---

### Test 3: Recovery via Retry

1. While the error dialog is still open, start the daemon in a separate terminal:
   ```bash
   ydotoold &
   ```
2. Click **Retry** on the dialog.
3. **Verify**:
   - The error dialog closes automatically.
   - The main CodeTyper window opens and is ready to use.

---

### Test 4: Missing Binary Check (Simulated PATH)

1. Run the app with an empty PATH to simulate `ydotool` not being installed:
   ```bash
   PATH=/tmp python3 app.py
   ```
2. **Verify**:
   - The dialog appears with the distinct binary-missing message:
     `ydotool is not installed or not in PATH.`
   - This message is distinct from the daemon-not-running message.

---

### Test 5: End-to-End Typing via ARM & TYPE

1. Ensure `ydotoold` is running:
   ```bash
   pgrep ydotoold || ydotoold &
   ```
2. Launch the app:
   ```bash
   python3 app.py
   ```
3. Paste a sample snippet into the editor:
   ```python
   def greet(name: str) -> str:
       return f"Hello, {name}!"
   ```
4. Set Delay to **5 ms**.
5. Click **ARM & TYPE**.
6. **Verify**:
   - Status bar updates to: `Status: Typed 57 characters.`
   - If an input field in another window had focus, the keystrokes are typed directly into it.
