"""
ydotool input backend for CodeTyper.
Provides binary and daemon health checks and character-by-character text typing.
"""

import os
import shutil
import subprocess


class BackendUnavailableError(Exception):
    """Raised when ydotool/ydotoold is not available or not reachable."""

    pass


class YdotoolBackend:
    """Backend interface for interacting with ydotool and ydotoold."""

    def is_available(self) -> tuple[bool, str]:
        """
        Returns (True, "") if ydotool binary exists AND ydotoold is reachable.
        Returns (False, reason) otherwise, where reason explains what's wrong.
        """
        # 1. Check if ydotool binary exists in PATH
        binary_path = shutil.which("ydotool")
        if not binary_path:
            return False, "ydotool is not installed or not in PATH."

        # 2. Check if ydotoold daemon is reachable and responding
        try:
            res = subprocess.run(
                ["ydotool", "mousemove", "--", "0", "0"],
                capture_output=True,
                text=True,
                timeout=1.5,
            )
            if res.returncode != 0:
                err = res.stderr.strip() if res.stderr else f"exit code {res.returncode}"
                return (
                    False,
                    f"ydotoold is not running or socket is inaccessible ({err}).\n"
                    "Start it with: ydotoold &",
                )
        except subprocess.TimeoutExpired:
            return (
                False,
                "ydotoold check timed out.\n"
                "Ensure ydotoold is running and responsive (ydotoold &).",
            )
        except FileNotFoundError:
            return False, "ydotool is not installed or not in PATH."
        except Exception as e:
            return (
                False,
                f"Failed to communicate with ydotoold ({e}).\n"
                "Start it with: ydotoold &",
            )

        return True, ""

    def type_text(self, text: str, delay_ms: int) -> None:
        """
        Sends `text` via `ydotool type --key-delay {delay_ms} -- {text}`.
        Raises BackendUnavailableError if the call fails.
        """
        if not text:
            return

        cmd = ["ydotool", "type", "--key-delay", str(delay_ms), "--", text]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                err_detail = result.stderr.strip() if result.stderr else f"exit code {result.returncode}"
                raise BackendUnavailableError(f"ydotool failed ({err_detail})")
        except FileNotFoundError as e:
            raise BackendUnavailableError("ydotool binary not found in PATH") from e
        except subprocess.TimeoutExpired as e:
            raise BackendUnavailableError("ydotool typing operation timed out after 30s") from e
        except BackendUnavailableError:
            raise
        except Exception as e:
            raise BackendUnavailableError(f"Unexpected error executing ydotool: {e}") from e
