"""
Countdown overlay component for CodeTyper.
Provides a non-blocking full-window overlay with countdown ticks and cancellation.
"""

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk


class CountdownOverlay(Gtk.Overlay):
    """
    Wraps the main content and adds a semi-transparent full-window overlay
    widget on top, shown/hidden on demand during countdown before typing.
    """

    def __init__(self, child_widget: Gtk.Widget) -> None:
        super().__init__()
        self.set_child(child_widget)

        self._timer_id: Optional[int] = None
        self._remaining = 0
        self._on_tick: Optional[Callable[[int], None]] = None
        self._on_complete: Optional[Callable[[], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None

        # Build overlay container
        self.overlay_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.overlay_box.set_halign(Gtk.Align.FILL)
        self.overlay_box.set_valign(Gtk.Align.FILL)
        self.overlay_box.set_hexpand(True)
        self.overlay_box.set_vexpand(True)
        self.overlay_box.add_css_class("countdown-overlay-box")

        # Centered inner content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_hexpand(True)
        content_box.set_vexpand(True)

        self.number_label = Gtk.Label(label="")
        self.number_label.add_css_class("countdown-number")
        content_box.append(self.number_label)

        self.subtitle_label = Gtk.Label(label="Focus target now")
        self.subtitle_label.add_css_class("countdown-subtitle")
        content_box.append(self.subtitle_label)

        self.cancel_button = Gtk.Button(label="Cancel")
        self.cancel_button.add_css_class("countdown-cancel-btn")
        self.cancel_button.connect("clicked", lambda _: self.cancel())
        content_box.append(self.cancel_button)

        self.overlay_box.append(content_box)
        self.add_overlay(self.overlay_box)
        self.overlay_box.set_visible(False)

    def start(
        self,
        seconds: int,
        on_tick: Optional[Callable[[int], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Start the countdown. If seconds <= 0, skips overlay and triggers on_complete.
        """
        if seconds <= 0:
            if on_complete:
                on_complete()
            return

        self._remaining = seconds
        self._on_tick = on_tick
        self._on_complete = on_complete
        self._on_cancel = on_cancel

        self.number_label.set_text(str(self._remaining))
        self.overlay_box.set_visible(True)

        if self._on_tick:
            self._on_tick(self._remaining)

        self._timer_id = GLib.timeout_add_seconds(1, self._on_tick_timer)

    def cancel(self) -> None:
        """Cancel an active countdown and invoke the on_cancel callback."""
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

        self.overlay_box.set_visible(False)
        if self._on_cancel:
            self._on_cancel()

    def _on_tick_timer(self) -> bool:
        """Internal GLib tick callback."""
        self._remaining -= 1
        if self._remaining > 0:
            self.number_label.set_text(str(self._remaining))
            if self._on_tick:
                self._on_tick(self._remaining)
            return True

        self._timer_id = None
        self.overlay_box.set_visible(False)
        if self._on_complete:
            self._on_complete()
        return False
