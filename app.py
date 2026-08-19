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

from backend.ydotool import YdotoolBackend
from ui.dialogs import BackendErrorDialog
from ui.main_window import CodeTyperWindow


class CodeTyperApp(Gtk.Application):
    """Gtk.Application controller for CodeTyper."""

    def __init__(self) -> None:
        super().__init__(
            application_id="com.local.codetyper",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.backend = YdotoolBackend()
        self.window = None
        self.error_dialog = None

    def do_startup(self) -> None:
        """Called when the application starts; load CSS resources."""
        Gtk.Application.do_startup(self)
        self._load_css()

    def do_activate(self) -> None:
        """Called on application activation; runs health check before showing window."""
        is_ok, reason = self.backend.is_available()
        if not is_ok:
            self._show_error_dialog(reason)
            return

        self._show_main_window()

    def _show_main_window(self) -> None:
        """Instantiate and present the main CodeTyper window."""
        if not self.window:
            self.window = CodeTyperWindow(application=self, backend=self.backend)
        self.window.present()

    def _show_error_dialog(self, reason: str) -> None:
        """Display the modal backend error dialog."""
        if not self.error_dialog:
            self.error_dialog = BackendErrorDialog(reason=reason)
            self.error_dialog.set_application(self)
            self.error_dialog.connect("response", self._on_dialog_response)
        else:
            self.error_dialog.set_reason(reason)

        self.error_dialog.present()

    def _on_dialog_response(self, dialog: Gtk.Dialog, response_id: int) -> None:
        """Handle Retry and Quit responses from the error dialog."""
        if response_id == Gtk.ResponseType.APPLY:  # Retry
            is_ok, reason = self.backend.is_available()
            if is_ok:
                dialog.close()
                self.error_dialog = None
                self._show_main_window()
            else:
                dialog.set_reason(reason)
        else:  # Quit or closed
            dialog.close()
            self.quit()

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
