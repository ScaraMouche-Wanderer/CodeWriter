"""
Typing engine for CodeTyper.
Orchestrates sending text to the ydotool backend in measured chunks on a
background thread with progress reporting and safe inter-chunk cancellation.
"""

import threading
from typing import Callable, Optional

from gi.repository import GLib

from backend.ydotool import BackendUnavailableError, YdotoolBackend


def calculate_chunk_size(delay_ms: int, target_ms: int = 400) -> int:
    """
    Returns number of characters per chunk such that a chunk sent at
    delay_ms per character takes approximately target_ms milliseconds.

    Clamped to [20, 200]:
    - Floor of 20: avoids excessive subprocess spawning overhead at slow delays.
    - Ceiling of 200: caps worst-case unresponsiveness between progress updates
      and keeps individual subprocess calls short enough to cancel promptly.
    """
    raw = target_ms / max(delay_ms, 1)
    return max(20, min(200, int(raw)))


class TypingController:
    """
    Orchestrates sending processed text to the ydotool backend in chunks,
    on a background thread, with progress reporting and cancellation.
    All callbacks are dispatched onto the GTK main loop via GLib.idle_add.
    """

    def __init__(self, backend: YdotoolBackend) -> None:
        self._backend = backend
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(
        self,
        text: str,
        delay_ms: int,
        on_progress: Callable[[int, int], None],
        on_complete: Callable[[int], None],
        on_cancelled: Callable[[int], None],
        on_error: Callable[[str], None],
    ) -> None:
        """
        Starts typing on a background thread and returns immediately.
        Callbacks are invoked safely on the GTK main thread via GLib.idle_add.
        """
        if not text:
            GLib.idle_add(on_complete, 0)
            return

        self._cancel_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            args=(text, delay_ms, on_progress, on_complete, on_cancelled, on_error),
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        """
        Sets the internal cancel flag.
        The background thread checks this flag between chunks and halts before
        sending the next chunk, calling on_cancelled with characters sent so far.
        """
        self._cancel_event.set()

    def is_running(self) -> bool:
        """Returns True if a typing thread is currently active."""
        return self._thread is not None and self._thread.is_alive()

    def _run(
        self,
        text: str,
        delay_ms: int,
        on_progress: Callable[[int, int], None],
        on_complete: Callable[[int], None],
        on_cancelled: Callable[[int], None],
        on_error: Callable[[str], None],
    ) -> None:
        """Background worker thread execution."""
        chunk_size = calculate_chunk_size(delay_ms)
        total = len(text)
        sent = 0

        try:
            while sent < total:
                # Cancellation is checked strictly BETWEEN chunks (bounded latency ~400ms)
                if self._cancel_event.is_set():
                    GLib.idle_add(on_cancelled, sent)
                    return

                chunk = text[sent : sent + chunk_size]
                self._backend.type_text(chunk, delay_ms)
                sent += len(chunk)

                # Passing sent and total as distinct arguments ensures immutable value capture
                GLib.idle_add(on_progress, sent, total)

            GLib.idle_add(on_complete, sent)
        except BackendUnavailableError as e:
            GLib.idle_add(on_error, str(e))
        except Exception as e:
            GLib.idle_add(on_error, f"Unexpected typing error: {e}")
        finally:
            self._cancel_event.clear()
            self._thread = None
