"""
Unit tests for core.typing_engine (chunk size calculation and TypingController).
"""

import time
from typing import Callable, Optional
from gi.repository import GLib

from backend.ydotool import BackendUnavailableError
from core.typing_engine import TypingController, calculate_chunk_size


def _drain_glib_events() -> None:
    """Helper to process pending GLib idle_add events in testing context."""
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


def test_calculate_chunk_size_clamping() -> None:
    """Test chunk size formula clamping at extremes and mid-range values."""
    # Ceiling clamping (200 chars max)
    assert calculate_chunk_size(delay_ms=0) == 200
    assert calculate_chunk_size(delay_ms=1) == 200
    assert calculate_chunk_size(delay_ms=2) == 200

    # Mid-range values
    assert calculate_chunk_size(delay_ms=4) == 100
    assert calculate_chunk_size(delay_ms=8) == 50
    assert calculate_chunk_size(delay_ms=10) == 40
    assert calculate_chunk_size(delay_ms=16) == 25
    assert calculate_chunk_size(delay_ms=20) == 20

    # Floor clamping (20 chars min)
    assert calculate_chunk_size(delay_ms=30) == 20
    assert calculate_chunk_size(delay_ms=50) == 20
    assert calculate_chunk_size(delay_ms=100) == 20


class MockBackend:
    def __init__(self, delay_per_call: float = 0.01, on_chunk: Optional[Callable[[], None]] = None) -> None:
        self.chunks = []
        self.delay_per_call = delay_per_call
        self.on_chunk = on_chunk

    def type_text(self, text: str, delay_ms: int) -> None:
        if self.delay_per_call > 0:
            time.sleep(self.delay_per_call)
        self.chunks.append((text, delay_ms))
        if self.on_chunk:
            self.on_chunk()


def test_typing_controller_chunked_run() -> None:
    """Test background typing controller chunks text and fires progress/complete callbacks."""
    backend = MockBackend(delay_per_call=0.002)
    controller = TypingController(backend)

    progress_events = []
    complete_events = []
    cancelled_events = []
    error_events = []

    # 120 chars at delay_ms=8 -> chunk_size=50 -> 3 chunks: 50, 50, 20
    text_to_type = "x" * 120
    controller.start(
        text=text_to_type,
        delay_ms=8,
        on_progress=lambda sent, total: progress_events.append((sent, total)),
        on_complete=lambda total: complete_events.append(total),
        on_cancelled=lambda sent: cancelled_events.append(sent),
        on_error=lambda msg: error_events.append(msg),
    )

    # Wait for thread completion
    while controller.is_running():
        _drain_glib_events()
        time.sleep(0.005)
    _drain_glib_events()

    assert len(backend.chunks) == 3
    assert [len(c[0]) for c in backend.chunks] == [50, 50, 20]
    assert progress_events == [(50, 120), (100, 120), (120, 120)]
    assert complete_events == [120]
    assert len(cancelled_events) == 0
    assert len(error_events) == 0


def test_typing_controller_cancellation() -> None:
    """Test cancelling between chunks halts execution and triggers on_cancelled."""
    controller = None

    def cancel_after_first_chunk():
        if controller:
            controller.cancel()

    backend = MockBackend(delay_per_call=0.01, on_chunk=cancel_after_first_chunk)
    controller = TypingController(backend)

    progress_events = []
    complete_events = []
    cancelled_events = []

    # 200 chars at delay_ms=8 -> chunk_size=50 -> 4 chunks
    text_to_type = "a" * 200
    controller.start(
        text=text_to_type,
        delay_ms=8,
        on_progress=lambda sent, total: progress_events.append((sent, total)),
        on_complete=lambda total: complete_events.append(total),
        on_cancelled=lambda sent: cancelled_events.append(sent),
        on_error=lambda msg: None,
    )

    while controller.is_running():
        _drain_glib_events()
        time.sleep(0.005)
    _drain_glib_events()

    assert len(complete_events) == 0
    assert len(cancelled_events) == 1
    # Successfully halted right after first chunk of 50 chars
    assert cancelled_events[0] == 50
    assert len(backend.chunks) == 1


def test_typing_controller_error_handling() -> None:
    """Test backend error is captured and forwarded to on_error callback."""
    class FailingBackend:
        def type_text(self, text: str, delay_ms: int) -> None:
            raise BackendUnavailableError("Simulated daemon crash")

    controller = TypingController(FailingBackend())
    error_events = []
    complete_events = []

    controller.start(
        text="error text",
        delay_ms=5,
        on_progress=lambda s, t: None,
        on_complete=lambda t: complete_events.append(t),
        on_cancelled=lambda s: None,
        on_error=lambda msg: error_events.append(msg),
    )

    while controller.is_running():
        _drain_glib_events()
        time.sleep(0.005)
    _drain_glib_events()

    assert len(complete_events) == 0
    assert len(error_events) == 1
    assert "Simulated daemon crash" in error_events[0]
