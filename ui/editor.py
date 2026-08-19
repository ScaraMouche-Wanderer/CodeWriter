"""
Code editor widget for CodeTyper.
Wraps GtkSourceView 5 inside a Gtk.ScrolledWindow with line numbers and monospace font.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, GtkSource


class CodeEditor(Gtk.ScrolledWindow):
    """
    Scrollable code editor component wrapping GtkSourceView and GtkSourceBuffer.
    Provides convenience methods for accessing and mutating code text.
    """

    def __init__(self) -> None:
        super().__init__()

        # Configure scrolled window container
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_min_content_height(300)
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

    def get_text(self) -> str:
        """Return the current full text from the editor buffer."""
        start_iter, end_iter = self.buffer.get_bounds()
        return self.buffer.get_text(start_iter, end_iter, True)

    def set_text(self, text: str) -> None:
        """Set the content of the editor buffer."""
        self.buffer.set_text(text)

    def get_buffer(self) -> GtkSource.Buffer:
        """Get the underlying GtkSource.Buffer instance."""
        return self.buffer

    def get_view(self) -> GtkSource.View:
        """Get the underlying GtkSource.View instance."""
        return self.view
