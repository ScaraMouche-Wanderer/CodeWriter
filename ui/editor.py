"""
Code editor widget for CodeTyper.
Wraps GtkSourceView 5 inside a Gtk.ScrolledWindow with syntax highlighting,
line numbers, selection awareness, clipboard operations, file loading,
and drag-and-drop support.
"""

import os
from typing import List, Optional, Tuple

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gdk, Gio, GLib, Gtk, GtkSource

SUPPORTED_LANGUAGES: List[Tuple[str, str]] = [
    ("Plain Text", "plain"),
    ("Python", "python"),
    ("C", "c"),
    ("C++", "cpp"),
    ("Rust", "rust"),
    ("Go", "go"),
    ("Java", "java"),
    ("JavaScript", "javascript"),
    ("TypeScript", "typescript"),
    ("Bash / Shell", "sh"),
    ("JSON", "json"),
    ("YAML", "yaml"),
    ("TOML", "toml"),
    ("Markdown", "markdown"),
    ("HTML", "html"),
    ("CSS", "css"),
    ("SQL", "sql"),
    ("Ruby", "ruby"),
    ("PHP", "php"),
    ("Kotlin", "kotlin"),
    ("Swift", "swift"),
    ("Lua", "lua"),
]

# Map file extensions to GtkSourceView language IDs
EXTENSION_TO_LANG_ID: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".sh": "sh",
    ".bash": "sh",
    ".zsh": "sh",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "css",
    ".sql": "sql",
    ".rb": "ruby",
    ".php": "php",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".lua": "lua",
    ".txt": "plain",
}


def detect_language_from_path(filepath: str) -> str:
    """
    Detect language ID from file extension.
    Returns 'plain' if no match is found.
    """
    _, ext = os.path.splitext(filepath.lower())
    return EXTENSION_TO_LANG_ID.get(ext, "plain")


class CodeEditor(Gtk.ScrolledWindow):
    """
    Scrollable code editor component wrapping GtkSourceView and GtkSourceBuffer.
    Provides syntax highlighting, selection inspection, editing conveniences,
    file loading, and drag-and-drop support.
    """

    def __init__(self) -> None:
        super().__init__()

        # Configure scrolled window container
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_min_content_height(80)
        self.set_min_content_width(120)
        self.add_css_class("editor-container")


        # Initialize GtkSourceBuffer & GtkSourceView
        self.buffer = GtkSource.Buffer()
        self.view = GtkSource.View.new_with_buffer(self.buffer)

        # Editor configuration
        self.view.set_show_line_numbers(True)
        self.view.set_monospace(True)
        self.view.set_tab_width(4)
        self.view.set_insert_spaces_instead_of_tabs(True)
        self.view.set_highlight_current_line(True)
        self.view.set_hexpand(True)
        self.view.set_vexpand(True)
        self.view.add_css_class("code-editor-view")

        # Attach view to scrolled window
        self.set_child(self.view)

        # Default language and font settings
        self._current_lang_id: str = "plain"
        self._loaded_filepath: Optional[str] = None
        self._font_size: int = 11
        self._word_wrap: bool = False
        self._css_provider = Gtk.CssProvider()
        self.view.get_style_context().add_provider(
            self._css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self._apply_font_size()

        # Set up drag-and-drop target for files
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_file_dropped)
        self.view.add_controller(drop_target)

    def _apply_font_size(self) -> None:
        """Apply the current font size to the editor view via CSS."""
        css = f"textview {{ font-size: {self._font_size}pt; }}"
        self._css_provider.load_from_data(css.encode("utf-8"))

    def set_font_size(self, size_pt: int) -> None:
        """Set the editor font size in points."""
        self._font_size = max(7, min(36, size_pt))
        self._apply_font_size()

    def get_font_size(self) -> int:
        """Return the current editor font size in points."""
        return self._font_size

    def zoom_in(self) -> int:
        """Increase editor font size by 1pt."""
        self.set_font_size(self._font_size + 1)
        return self._font_size

    def zoom_out(self) -> int:
        """Decrease editor font size by 1pt."""
        self.set_font_size(self._font_size - 1)
        return self._font_size

    def reset_zoom(self) -> int:
        """Reset editor font size to default (11pt)."""
        self.set_font_size(11)
        return self._font_size

    def toggle_word_wrap(self) -> bool:
        """Toggle soft word wrap and return the new state."""
        self._word_wrap = not self._word_wrap
        self.view.set_wrap_mode(
            Gtk.WrapMode.WORD_CHAR if self._word_wrap else Gtk.WrapMode.NONE
        )
        return self._word_wrap

    def set_word_wrap(self, enable: bool) -> None:
        """Enable or disable soft word wrap."""
        self._word_wrap = enable
        self.view.set_wrap_mode(
            Gtk.WrapMode.WORD_CHAR if self._word_wrap else Gtk.WrapMode.NONE
        )

    def is_word_wrap_enabled(self) -> bool:
        """Return whether word wrap is currently active."""
        return self._word_wrap

    def set_highlight_current_line(self, enable: bool) -> None:
        """Toggle current line highlighting in the editor view."""
        self.view.set_highlight_current_line(enable)

    def set_show_line_numbers(self, enable: bool) -> None:
        """Toggle line numbers gutter display."""
        self.view.set_show_line_numbers(enable)

    # ── Line Manipulation Helpers ──

    def _get_line_iter(self, line_num: int) -> Gtk.TextIter:
        """Helper to get a valid Gtk.TextIter at the given line number."""
        res = self.buffer.get_iter_at_line(line_num)
        return res[1] if isinstance(res, tuple) else res

    def duplicate_current_line_or_selection(self) -> None:
        """Duplicate the selected text or current line."""

        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start_iter, end_iter = bounds
            selected_text = self.buffer.get_text(start_iter, end_iter, True)
            self.buffer.insert(end_iter, selected_text)
        else:
            insert_mark = self.buffer.get_insert()
            cursor_iter = self.buffer.get_iter_at_mark(insert_mark)
            line_num = cursor_iter.get_line()
            start_line = self._get_line_iter(line_num)
            end_line = start_line.copy()
            if not end_line.ends_line():
                end_line.forward_to_line_end()
            line_text = self.buffer.get_text(start_line, end_line, True)
            end_line.forward_line()
            self.buffer.insert(end_line, line_text + "\n")

    def delete_current_line(self) -> None:
        """Delete the line under the cursor."""
        insert_mark = self.buffer.get_insert()
        cursor_iter = self.buffer.get_iter_at_mark(insert_mark)
        line_num = cursor_iter.get_line()
        start_line = self._get_line_iter(line_num)
        end_line = start_line.copy()
        if not end_line.forward_line():
            end_line.forward_to_line_end()
        self.buffer.delete(start_line, end_line)

    def move_current_line(self, direction: int) -> None:
        """
        Move the line under cursor up (direction=-1) or down (direction=1).
        """
        insert_mark = self.buffer.get_insert()
        cursor_iter = self.buffer.get_iter_at_mark(insert_mark)
        line_num = cursor_iter.get_line()
        total_lines = self.buffer.get_line_count()

        target_line_num = line_num + direction
        if target_line_num < 0 or target_line_num >= total_lines:
            return

        # Read current line
        curr_start = self._get_line_iter(line_num)
        curr_end = curr_start.copy()
        if not curr_end.forward_line():
            curr_end.forward_to_line_end()
        curr_text = self.buffer.get_text(curr_start, curr_end, True)
        if not curr_text.endswith("\n"):
            curr_text += "\n"

        self.buffer.delete(curr_start, curr_end)

        dest_iter = self._get_line_iter(target_line_num)
        self.buffer.insert(dest_iter, curr_text)

        # Place cursor on the new line position
        new_iter = self._get_line_iter(target_line_num)
        self.buffer.place_cursor(new_iter)


    # ── Callbacks for drag-and-drop ──
    _on_file_load_callback = None

    def set_on_file_load(self, callback) -> None:
        """Set a callback(filepath, lang_id) to be called after a file is loaded."""
        self._on_file_load_callback = callback

    def _on_file_dropped(self, drop_target, value, x, y) -> bool:
        """Handle a file being dropped onto the editor."""
        if isinstance(value, Gio.File):
            filepath = value.get_path()
            if filepath:
                self.load_file(filepath)
                return True
        return False

    def load_file(self, filepath: str) -> bool:
        """
        Load a file into the editor buffer.
        Auto-detects language from file extension.
        Returns True on success, False on error.
        """
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.buffer.set_text(content)
            self._loaded_filepath = filepath

            lang_id = detect_language_from_path(filepath)
            self.set_language(lang_id)

            if self._on_file_load_callback:
                self._on_file_load_callback(filepath, lang_id)
            return True
        except Exception:
            return False

    def save_file(self, filepath: Optional[str] = None) -> bool:
        """
        Save editor content to a file.
        Uses the last loaded filepath if none provided.
        Returns True on success, False on error.
        """
        target = filepath or self._loaded_filepath
        if not target:
            return False
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(self.get_text())
            self._loaded_filepath = target
            return True
        except Exception:
            return False

    def get_loaded_filepath(self) -> Optional[str]:
        """Return the path of the last loaded/saved file."""
        return self._loaded_filepath

    def get_text(self) -> str:
        """Return the current full text from the editor buffer."""
        start_iter, end_iter = self.buffer.get_bounds()
        return self.buffer.get_text(start_iter, end_iter, True)

    def set_text(self, text: str) -> None:
        """Set the content of the editor buffer."""
        self.buffer.set_text(text)

    def get_selected_text(self) -> Optional[str]:
        """
        Returns currently highlighted text if selection is active,
        or None if no text is selected.
        """
        bounds = self.buffer.get_selection_bounds()
        if bounds:
            start_iter, end_iter = bounds
            return self.buffer.get_text(start_iter, end_iter, True)
        return None

    def get_stats(self) -> dict:
        """Return buffer metrics (lines, characters, and selected characters)."""
        full_text = self.get_text()
        lines = self.buffer.get_line_count()
        chars = len(full_text)
        sel = self.get_selected_text()
        return {
            "lines": lines if chars > 0 else 0,
            "chars": chars,
            "selected_chars": len(sel) if sel else 0,
        }

    def set_language(self, lang_id: str) -> None:
        """Apply syntax highlighting for the given language ID."""
        self._current_lang_id = lang_id or "plain"
        if lang_id and lang_id != "plain":
            lm = GtkSource.LanguageManager.get_default()
            lang = lm.get_language(lang_id)
            self.buffer.set_language(lang)
            self.buffer.set_highlight_syntax(True)
        else:
            self.buffer.set_language(None)
            self.buffer.set_highlight_syntax(False)

    def get_language_id(self) -> str:
        """Return the current language ID."""
        return self._current_lang_id

    def copy_clipboard(self) -> None:
        """Copy current selection (or full buffer) to clipboard."""
        text = self.get_selected_text() or self.get_text()
        if text:
            display = Gdk.Display.get_default()
            if display:
                clipboard = display.get_clipboard()
                clipboard.set(text)

    def paste_clipboard(self) -> None:
        """Paste clipboard content into the current cursor position."""
        display = Gdk.Display.get_default()
        if display:
            clipboard = display.get_clipboard()
            clipboard.read_text_async(None, self._on_clipboard_text_read)

    def _on_clipboard_text_read(self, clipboard, result) -> None:
        try:
            text = clipboard.read_text_finish(result)
            if text:
                bounds = self.buffer.get_selection_bounds()
                if bounds:
                    start_iter, end_iter = bounds
                    self.buffer.delete(start_iter, end_iter)
                self.buffer.insert_at_cursor(text)
        except Exception:
            pass

    def clear(self) -> None:
        """Clear all content from the editor buffer."""
        self.buffer.set_text("")
        self._loaded_filepath = None

    def get_buffer(self) -> GtkSource.Buffer:
        """Get the underlying GtkSource.Buffer instance."""
        return self.buffer

    def get_view(self) -> GtkSource.View:
        """Get the underlying GtkSource.View instance."""
        return self.view

