"""
ydotool input backend for CodeTyper.
Provides binary and daemon health checks and character-by-character text typing.
"""

import os
import shutil
import socket
import subprocess
import time
from typing import Optional


class BackendUnavailableError(Exception):
    """Raised when ydotool/ydotoold is not available or not reachable."""

    pass


class YdotoolBackend:
    """Backend interface for interacting with ydotool and ydotoold."""

    def __init__(self, cache_ttl: float = 1.5) -> None:
        self._cache_ttl = cache_ttl
        self._cached_available: Optional[tuple[bool, str]] = None
        self._last_check_time: float = 0.0

    def is_available(self, force: bool = False) -> tuple[bool, str]:
        """
        Returns (True, "") if ydotool binary exists AND ydotoold is reachable.
        Returns (False, reason) otherwise, where reason explains what's wrong.
        Caches result for `cache_ttl` seconds to avoid socket spam on rapid checks.
        """
        now = time.time()
        if not force and self._cached_available is not None and (now - self._last_check_time) < self._cache_ttl:
            return self._cached_available

        result = self._check_availability()
        self._cached_available = result
        self._last_check_time = now
        return result

    def _check_availability(self) -> tuple[bool, str]:
        """Performs actual socket and binary validation with zero input side-effects."""
        # 1. Check if ydotool binary exists in PATH
        binary_path = shutil.which("ydotool")
        if not binary_path:
            return False, "ydotool is not installed or not in PATH."

        # 2. Check if ydotoold daemon socket exists and is reachable
        socket_candidates = [
            os.environ.get("YDOTOOL_SOCKET"),
            f"/run/user/{os.getuid()}/.ydotool_socket",
            "/tmp/.ydotool_socket",
            "/run/ydotoold/ydotoold.socket",
        ]
        socket_found = None
        for path in socket_candidates:
            if path and os.path.exists(path):
                socket_found = path
                break

        if not socket_found:
            return (
                False,
                "ydotoold is not running or socket is inaccessible.\n"
                "Start it with: ydotoold &",
            )

        # Passive UNIX domain socket check with zero input side-effects
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            sock.connect(socket_found)
            sock.close()
        except Exception as e:
            return (
                False,
                f"ydotoold socket at {socket_found} is unreachable ({e}).\n"
                "Start it with: ydotoold &",
            )

        return True, ""

    def type_text(self, text: str, delay_ms: int) -> None:
        """
        Sends `text` via `ydotool type --key-delay {delay_ms} -- {text}`.
        Automatically retries once after a short backoff on transient failure.
        Raises BackendUnavailableError if the call fails after retry.
        """
        if not text:
            return

        cmd = ["ydotool", "type", "--key-delay", str(delay_ms), "--", text]
        last_error = None

        for attempt in range(2):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    return
                err_detail = result.stderr.strip() if result.stderr else f"exit code {result.returncode}"
                last_error = BackendUnavailableError(f"ydotool failed ({err_detail})")
            except FileNotFoundError as e:
                raise BackendUnavailableError("ydotool binary not found in PATH") from e
            except subprocess.TimeoutExpired as e:
                last_error = BackendUnavailableError("ydotool typing operation timed out after 30s")
            except Exception as e:
                last_error = BackendUnavailableError(f"Unexpected error executing ydotool: {e}")

            if attempt == 0:
                time.sleep(0.08)

        if last_error:
            raise last_error

    def send_backspace(self, count: int = 1, delay_ms: int = 10) -> None:
        """
        Sends hardware Backspace key events (keycode 14) via ydotool key.
        Used for realistic typo correction.
        """
        if count <= 0:
            return

        key_args = []
        for _ in range(count):
            key_args.extend(["14:1", "14:0"])

        cmd = ["ydotool", "key", "--key-delay", str(max(1, delay_ms)), "--"] + key_args
        last_error = None

        for attempt in range(2):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return
                err_detail = result.stderr.strip() if result.stderr else f"exit code {result.returncode}"
                last_error = BackendUnavailableError(f"ydotool key backspace failed ({err_detail})")
            except FileNotFoundError as e:
                raise BackendUnavailableError("ydotool binary not found in PATH") from e
            except Exception as e:
                last_error = BackendUnavailableError(f"Unexpected error executing ydotool key: {e}")

            if attempt == 0:
                time.sleep(0.05)

        if last_error:
            raise last_error

