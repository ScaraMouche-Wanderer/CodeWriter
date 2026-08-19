"""
ydotool input backend for CodeTyper.
Provides binary and daemon health checks and character-by-character text typing.
"""

import os
import shutil
import socket
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
        Performs socket validation with zero observable side-effects (no mouse move).
        """
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
