"""
Multi-tab manager for CodeTyper.
Manages multiple CodeEditor instances in a tab-like interface using Gtk.Notebook.
"""

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from ui.editor import CodeEditor

MAX_TABS = 8


class TabManager(Gtk.Box):
    """
    Manages a tab bar and a Gtk.Notebook of CodeEditor instances.
    Supports adding, closing, and switching tabs with a maximum of MAX_TABS.
    """

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._editors: list[CodeEditor] = []
        self._on_tab_changed_callback: Optional[Callable[[CodeEditor, int], None]] = None
        self._editor_config = {
            "font_size": 11,
            "show_line_numbers": True,
            "word_wrap": False,
            "highlight_current_line": True,
        }

        # ── Scrollable Tab Bar ──
        self._tab_bar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=0,
            css_classes=["tab-bar-box"],
        )
        self._tab_scroll = Gtk.ScrolledWindow(
            child=self._tab_bar,
            css_classes=["tab-scroll-window"],
            vscrollbar_policy=Gtk.PolicyType.NEVER,
            hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            hexpand=True,
            vexpand=False,
        )
        self.append(self._tab_scroll)

        # ── Notebook (hidden tabs, we draw our own) ──
        self._notebook = Gtk.Notebook()
        self._notebook.set_show_tabs(False)
        self._notebook.set_show_border(False)
        self._notebook.set_hexpand(True)
        self._notebook.set_vexpand(True)
        self.append(self._notebook)

        # Add initial tab
        self.add_tab()

    def configure_editors(
        self,
        font_size: int = 11,
        show_line_numbers: bool = True,
        word_wrap: bool = False,
        highlight_current_line: bool = True,
    ) -> None:
        """Update editor config and apply to all existing and future editors."""
        self._editor_config["font_size"] = font_size
        self._editor_config["show_line_numbers"] = show_line_numbers
        self._editor_config["word_wrap"] = word_wrap
        self._editor_config["highlight_current_line"] = highlight_current_line

        for ed in self._editors:
            ed.set_font_size(font_size)
            ed.set_show_line_numbers(show_line_numbers)
            ed.set_word_wrap(word_wrap)
            ed.set_highlight_current_line(highlight_current_line)

    def set_on_tab_changed(self, callback: Callable[[CodeEditor, int], None]) -> None:
        """Set a callback(editor, index) to be called when the active tab changes."""
        self._on_tab_changed_callback = callback

    def _notify_tab_changed(self) -> None:
        if self._on_tab_changed_callback:
            idx = self.get_active_index()
            editor = self.get_active_editor()
            self._on_tab_changed_callback(editor, idx)

    def add_tab(self, title: str = "Untitled") -> Optional[CodeEditor]:
        """Add a new tab. Returns the new editor, or None if at max."""
        if len(self._editors) >= MAX_TABS:
            return None

        editor = CodeEditor()
        editor.set_font_size(self._editor_config.get("font_size", 11))
        editor.set_show_line_numbers(self._editor_config.get("show_line_numbers", True))
        editor.set_word_wrap(self._editor_config.get("word_wrap", False))
        editor.set_highlight_current_line(self._editor_config.get("highlight_current_line", True))

        self._editors.append(editor)
        self._notebook.append_page(editor, None)

        # Track buffer changes for tab title updates
        editor.get_buffer().connect("changed", lambda _: self._update_tab_titles())

        self._rebuild_tab_bar()
        self._notebook.set_current_page(len(self._editors) - 1)
        self._notify_tab_changed()
        return editor


    def close_tab(self, index: int) -> bool:
        """Close a tab at given index. Won't close the last remaining tab."""
        if len(self._editors) <= 1 or index < 0 or index >= len(self._editors):
            return False

        editor = self._editors.pop(index)
        self._notebook.remove_page(index)

        self._rebuild_tab_bar()

        # Activate a valid tab
        new_idx = min(index, len(self._editors) - 1)
        self._notebook.set_current_page(new_idx)
        self._notify_tab_changed()
        return True

    def get_active_editor(self) -> CodeEditor:
        """Return the currently active CodeEditor."""
        idx = self._notebook.get_current_page()
        if 0 <= idx < len(self._editors):
            return self._editors[idx]
        return self._editors[0]

    def get_active_index(self) -> int:
        """Return the index of the currently active tab."""
        return self._notebook.get_current_page()

    def get_editor_count(self) -> int:
        """Return the number of open tabs."""
        return len(self._editors)

    def get_all_editors(self) -> list[CodeEditor]:
        """Return all managed CodeEditor instances."""
        return list(self._editors)


    def _rebuild_tab_bar(self) -> None:
        """Rebuild the tab bar buttons from scratch."""
        while child := self._tab_bar.get_first_child():
            self._tab_bar.remove(child)

        active_idx = self._notebook.get_current_page()

        for i, editor in enumerate(self._editors):
            tab_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL,
                spacing=0,
                css_classes=["tab-pill-box"] + (["tab-pill-active"] if i == active_idx else []),
            )

            title = self._get_tab_title(editor)
            tab_btn = Gtk.Button(
                label=title,
                css_classes=["tab-btn"] + (["tab-btn-active"] if i == active_idx else []),
            )
            tab_btn.connect("clicked", lambda _, idx=i: self._switch_to(idx))
            tab_box.append(tab_btn)

            if len(self._editors) > 1:
                close_btn = Gtk.Button(label="✕", css_classes=["tab-close-btn"])
                close_btn.set_tooltip_text("Close Tab")
                close_btn.connect("clicked", lambda _, idx=i: self.close_tab(idx))
                tab_box.append(close_btn)

            self._tab_bar.append(tab_box)

        # "+" add button
        if len(self._editors) < MAX_TABS:
            add_btn = Gtk.Button(label="+", css_classes=["tab-add-btn"])
            add_btn.set_tooltip_text("New Tab")
            add_btn.connect("clicked", lambda _: self.add_tab())
            self._tab_bar.append(add_btn)

    def _switch_to(self, index: int) -> None:
        """Switch to tab at index."""
        if 0 <= index < len(self._editors):
            self._notebook.set_current_page(index)
            self._rebuild_tab_bar()
            self._notify_tab_changed()

    def _get_tab_title(self, editor: CodeEditor) -> str:
        """Derive tab title from the first non-empty line of editor content or loaded file."""
        filepath = editor.get_loaded_filepath()
        if filepath:
            import os
            return os.path.basename(filepath)

        text = editor.get_text()
        if not text or not text.strip():
            return "Untitled"
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped:
                return stripped[:16] + ("…" if len(stripped) > 16 else "")
        return "Untitled"

    def _update_tab_titles(self) -> None:
        """Refresh tab bar labels when buffer content changes."""
        self._rebuild_tab_bar()
