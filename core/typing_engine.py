import random
import threading
import time
from typing import Callable, Optional

from gi.repository import GLib

from backend.ydotool import BackendUnavailableError, YdotoolBackend
from core.humanizer import calculate_char_delay, get_typo_character, should_trigger_typo


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
    on a background thread, with progress reporting, pause/resume, and cancellation.
    All callbacks are dispatched onto the GTK main loop via GLib.idle_add.
    """

    def __init__(self, backend: YdotoolBackend) -> None:
        self._backend = backend
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        self._thread: Optional[threading.Thread] = None

    def start(
        self,
        text: str,
        delay_ms: int,
        on_progress: Callable[[int, int], None],
        on_complete: Callable[[int], None],
        on_cancelled: Callable[[int], None],
        on_error: Callable[[str], None],
        enable_humanize: bool = False,
        typo_rate_pct: float = 0.0,
    ) -> None:
        """
        Starts typing on a background thread and returns immediately.
        Callbacks are invoked safely on the GTK main thread via GLib.idle_add.
        """
        if not text:
            GLib.idle_add(on_complete, 0)
            return

        self._cancel_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(
            target=self._run,
            args=(text, delay_ms, on_progress, on_complete, on_cancelled, on_error, enable_humanize, typo_rate_pct),
            daemon=True,
        )
        self._thread.start()

    def pause(self) -> None:
        """Pauses typing stream without aborting character position."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resumes typing stream from paused state."""
        self._pause_event.set()

    def is_paused(self) -> bool:
        """Returns True if the typing thread is active but paused."""
        return self.is_running() and not self._pause_event.is_set()

    def cancel(self) -> None:
        """
        Sets the internal cancel flag and unblocks pause if active.
        The background thread checks this flag between chunks and halts before
        sending the next chunk, calling on_cancelled with characters sent so far.
        """
        self._cancel_event.set()
        self._pause_event.set()  # Unblock thread if paused so it can exit cleanly

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
        enable_humanize: bool = False,
        typo_rate_pct: float = 0.0,
    ) -> None:
        """Background worker thread execution."""
        total = len(text)
        sent = 0

        try:
            if not enable_humanize:
                # Fast chunked execution
                chunk_size = calculate_chunk_size(delay_ms)
                while sent < total:
                    # Check pause state
                    while not self._pause_event.is_set():
                        if self._cancel_event.is_set():
                            GLib.idle_add(on_cancelled, sent)
                            return
                        time.sleep(0.04)

                    if self._cancel_event.is_set():
                        GLib.idle_add(on_cancelled, sent)
                        return

                    chunk = text[sent : sent + chunk_size]
                    self._backend.type_text(chunk, delay_ms)
                    sent += len(chunk)
                    GLib.idle_add(on_progress, sent, total)
            else:
                # Humanized cadence execution with jitter and realistic typo auto-corrections
                prev_char = ""
                idx = 0
                while idx < total:
                    # Check pause state
                    while not self._pause_event.is_set():
                        if self._cancel_event.is_set():
                            GLib.idle_add(on_cancelled, sent)
                            return
                        time.sleep(0.04)

                    if self._cancel_event.is_set():
                        GLib.idle_add(on_cancelled, sent)
                        return

                    # Form micro-bursts (up to next word boundary or newline)
                    end_idx = idx + 1
                    while end_idx < total and end_idx - idx < 12:
                        ch = text[end_idx - 1]
                        if ch in ("\n", " ", ";", "{", "}"):
                            break
                        end_idx += 1

                    sub_text = text[idx:end_idx]
                    first_char = sub_text[0]
                    char_delay = calculate_char_delay(delay_ms, first_char, prev_char, enable_humanize=True)

                    # Simulate realistic typo on the leading character if applicable
                    if (
                        typo_rate_pct > 0.0
                        and first_char.isalnum()
                        and should_trigger_typo(first_char, typo_rate_pct)
                    ):
                        typo_ch = get_typo_character(first_char)
                        if typo_ch:
                            # 1. Type the mistaken neighbor key
                            self._backend.type_text(typo_ch, int(char_delay))
                            # 2. Human cognitive reaction delay (80-180ms)
                            time.sleep(random.uniform(0.08, 0.18))
                            # 3. Hit hardware backspace
                            self._backend.send_backspace(1, delay_ms=10)
                            # 4. Short recovery pause
                            time.sleep(random.uniform(0.02, 0.05))

                    self._backend.type_text(sub_text, int(char_delay))
                    sent += len(sub_text)
                    idx = end_idx
                    prev_char = sub_text[-1]

                    GLib.idle_add(on_progress, sent, total)

            GLib.idle_add(on_complete, sent)
        except BackendUnavailableError as e:
            GLib.idle_add(on_error, str(e))
        except Exception as e:
            GLib.idle_add(on_error, f"Unexpected typing error: {e}")
        finally:
            self._cancel_event.clear()
            self._pause_event.set()
            self._thread = None

