#!/usr/bin/env python3
"""
Manual diagnostic script for ydotool.
Types 'hello from codewriter' into the active focused window.
"""

import subprocess
import sys
import time


def main() -> int:
    message = "hello from codewriter"
    countdown = 3

    print("=" * 60)
    print(" CodeWriter — ydotool Diagnostic Test")
    print("=" * 60)
    print(f"Target text: '{message}'")
    print(f"You have {countdown} seconds to switch focus to your target text field...\n")

    for i in range(countdown, 0, -1):
        print(f"Typing in {i}...", flush=True)
        time.sleep(1.0)

    print("\nSending keystrokes via ydotool...", flush=True)
    try:
        res = subprocess.run(
            ["ydotool", "type", message],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            print("[ PASS ] ydotool executed successfully.")
            return 0
        else:
            print(f"[ FAIL ] ydotool exited with code {res.returncode}:")
            if res.stderr:
                print(res.stderr.strip())
            return 1
    except FileNotFoundError:
        print("[ FAIL ] 'ydotool' command not found in PATH.")
        return 1
    except Exception as e:
        print(f"[ FAIL ] Error executing ydotool: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
