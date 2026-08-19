"""
ydotool input backend for CodeTyper.
Stub implementation for Phase 0 and Phase 1.
"""


class YdotoolBackend:
    """Backend interface for simulating keystrokes using ydotool."""

    def is_available(self) -> bool:
        """Check if ydotool binary and daemon are available."""
        raise NotImplementedError("YdotoolBackend.is_available() is implemented in Phase 2.")

    def type_text(self, text: str, delay_ms: int) -> None:
        """
        Type text character-by-character into the active window.

        :param text: Text string to type.
        :param delay_ms: Delay in milliseconds between keystrokes.
        """
        raise NotImplementedError("YdotoolBackend.type_text() is implemented in Phase 2.")
