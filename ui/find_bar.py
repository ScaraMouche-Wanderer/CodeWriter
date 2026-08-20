"""
Find & Replace bar for CodeTyper.
Uses GtkSource.SearchContext for efficient match highlighting.
"""

from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, GtkSource


class FindBar(Gtk.Revealer):
    """
    Toggleable find & replace bar that wraps GtkSource.SearchContext.
    Supports search, next/prev, replace, replace all, case toggle.
    """

    def __init__(self, source_buffer: GtkSource.Buffer) -> None:
        super().__init__()
        self.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.set_reveal_child(False)

        self._buffer = source_buffer
        self._search_settings = GtkSource.SearchSettings()
        self._search_settings.set_wrap_around(True)
        self._search_settings.set_case_sensitive(False)
        self._search_settings.set_regex_enabled(False)
        self._search_context = GtkSource.SearchContext.new(source_buffer, self._search_settings)
        self._search_context.set_highlight(True)

        self._replace_visible = False
        self._build_ui()

    def _build_ui(self) -> None:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, css_classes=["find-bar"])

        # ── Find Row ──
        find_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._find_entry = Gtk.Entry(
            placeholder_text="Find…",
            hexpand=True,
            css_classes=["find-entry"],
        )
        self._find_entry.connect("changed", self._on_find_changed)
        self._find_entry.connect("activate", lambda _: self.find_next())
        find_row.append(self._find_entry)

        self._match_label = Gtk.Label(label="", css_classes=["find-match-label"])
        find_row.append(self._match_label)

        self._case_toggle = Gtk.ToggleButton(label="Aa", css_classes=["find-case-toggle"])
        self._case_toggle.set_tooltip_text("Case Sensitive")
        self._case_toggle.connect("toggled", self._on_case_toggled)
        find_row.append(self._case_toggle)

        prev_btn = Gtk.Button(label="▲", css_classes=["find-btn"])
        prev_btn.set_tooltip_text("Previous (Shift+Enter)")
        prev_btn.connect("clicked", lambda _: self.find_prev())
        find_row.append(prev_btn)

        next_btn = Gtk.Button(label="▼", css_classes=["find-btn"])
        next_btn.set_tooltip_text("Next (Enter)")
        next_btn.connect("clicked", lambda _: self.find_next())
        find_row.append(next_btn)

        close_btn = Gtk.Button(label="✕", css_classes=["find-close-btn"])
        close_btn.set_tooltip_text("Close (Escape)")
        close_btn.connect("clicked", lambda _: self.hide_bar())
        find_row.append(close_btn)

        outer.append(find_row)

        # ── Replace Row ──
        self._replace_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self._replace_entry = Gtk.Entry(
            placeholder_text="Replace with…",
            hexpand=True,
            css_classes=["find-entry"],
        )
        self._replace_entry.connect("activate", lambda _: self.replace_next())
        self._replace_row.append(self._replace_entry)

        replace_btn = Gtk.Button(label="Replace", css_classes=["find-btn"])
        replace_btn.connect("clicked", lambda _: self.replace_next())
        self._replace_row.append(replace_btn)

        replace_all_btn = Gtk.Button(label="All", css_classes=["find-btn"])
        replace_all_btn.connect("clicked", lambda _: self.replace_all())
        self._replace_row.append(replace_all_btn)

        self._replace_row.set_visible(False)
        outer.append(self._replace_row)

        # Keyboard controller for Escape handling in the bar
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        outer.add_controller(key_ctrl)

        self.set_child(outer)

    def show_find(self) -> None:
        """Show find bar (without replace)."""
        self._replace_visible = False
        self._replace_row.set_visible(False)
        self.set_reveal_child(True)
        self._find_entry.grab_focus()

    def show_find_replace(self) -> None:
        """Show find bar with replace row."""
        self._replace_visible = True
        self._replace_row.set_visible(True)
        self.set_reveal_child(True)
        self._find_entry.grab_focus()

    def hide_bar(self) -> None:
        """Hide the find bar and clear highlights."""
        self.set_reveal_child(False)
        self._search_settings.set_search_text(None)
        self._match_label.set_text("")

    def is_visible_bar(self) -> bool:
        """Return whether the bar is currently revealed."""
        return self.get_reveal_child()

    def find_next(self) -> None:
        """Move to the next match."""
        cursor = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        found, start, end, wrapped = self._search_context.forward(cursor)
        if found:
            self._buffer.select_range(start, end)
            # Scroll the view — we need the view reference from parent
        self._update_match_count()

    def find_prev(self) -> None:
        """Move to the previous match."""
        cursor = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        found, start, end, wrapped = self._search_context.backward(cursor)
        if found:
            self._buffer.select_range(start, end)
        self._update_match_count()

    def replace_next(self) -> None:
        """Replace current match and move to next."""
        bounds = self._buffer.get_selection_bounds()
        if bounds:
            start, end = bounds
            replacement = self._replace_entry.get_text()
            try:
                self._search_context.replace(start, end, replacement, len(replacement.encode("utf-8")))
            except Exception:
                pass
        self.find_next()

    def replace_all(self) -> None:
        """Replace all matches."""
        replacement = self._replace_entry.get_text()
        try:
            self._search_context.replace_all(replacement, len(replacement.encode("utf-8")))
        except Exception:
            pass
        self._update_match_count()

    def _on_find_changed(self, entry: Gtk.Entry) -> None:
        text = entry.get_text()
        self._search_settings.set_search_text(text if text else None)
        if text:
            # Jump to first match from top
            start_iter = self._buffer.get_start_iter()
            found, match_start, match_end, wrapped = self._search_context.forward(start_iter)
            if found:
                self._buffer.select_range(match_start, match_end)
        self._update_match_count()

    def _on_case_toggled(self, button: Gtk.ToggleButton) -> None:
        self._search_settings.set_case_sensitive(button.get_active())
        self._update_match_count()

    def _update_match_count(self) -> None:
        count = self._search_context.get_occurrences_count()
        if count < 0:
            self._match_label.set_text("")
        elif count == 0:
            self._match_label.set_text("No matches")
        else:
            self._match_label.set_text(f"{count} match{'es' if count != 1 else ''}")

    def _on_key_pressed(self, _ctrl, keyval: int, _keycode: int, state) -> bool:
        from gi.repository import Gdk
        if keyval == Gdk.KEY_Escape:
            self.hide_bar()
            return True
        # Shift+Enter = find prev
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            if state & Gdk.ModifierType.SHIFT_MASK:
                self.find_prev()
            else:
                # Only handle Enter in find entry (replace entry has its own activate)
                pass
            return False
        return False
