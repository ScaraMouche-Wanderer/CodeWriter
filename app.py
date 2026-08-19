#!/usr/bin/env python3
"""
CodeTyper — Main Application Entry Point.
A native Linux utility for simulating typing into active windows via ydotool.
"""

import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gdk, Gio, Gtk

from ui.main_window import CodeTyperWindow


class CodeTyperApp(Gtk.Application):
    """Gtk.Application controller for CodeTyper."""

    def __init__(self) -> None:
        super().__init__(
            application_id="com.local.codetyper",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.window = None

    def do_startup(self) -> None:
        """Called when the application starts; load CSS resources."""
        Gtk.Application.do_startup(self)
        self._load_css()

    def do_activate(self) -> None:
        """Called when the application is activated; instantiate and present window."""
        if not self.window:
            self.window = CodeTyperWindow(application=self)
        self.window.present()

    def _load_css(self) -> None:
        """Load and apply stylesheet to the default display."""
        css_path = os.path.join(os.path.dirname(__file__), "resources", "style.css")
        if os.path.exists(css_path):
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )


def main() -> int:
    app = CodeTyperApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
