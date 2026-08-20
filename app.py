#!/usr/bin/env python3
"""
CodeWriter — Main Application Entry Point.
A native Linux utility for simulating typing into active windows via ydotool.
"""

import logging
import os
import sys
import traceback

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gdk, Gio, GLib, Gtk

from backend.ydotool import YdotoolBackend
from core.settings import SettingsStore
from ui.dialogs import BackendErrorDialog
from ui.main_window import CodeTyperWindow as CodeWriterWindow
from ui.tray import CodeWriterTray

logger = logging.getLogger("CodeWriter")

# Set program and application name for desktop environment / window manager identification
GLib.set_prgname("com.local.codewriter")
GLib.set_application_name("CodeWriter")


def _global_exception_handler(exctype, value, tb):
    """Top-level uncaught exception handler logging to stderr."""
    err_str = "".join(traceback.format_exception(exctype, value, tb))
    sys.stderr.write(f"\n[CodeWriter FATAL ERROR]\n{err_str}\n")
    sys.stderr.flush()


sys.excepthook = _global_exception_handler


class CodeWriterApp(Gtk.Application):
    """Gtk.Application controller for CodeWriter."""

    def __init__(self) -> None:
        super().__init__(
            application_id="com.local.codewriter",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.backend = YdotoolBackend()
        self.settings_store = SettingsStore()
        self.window = None
        self.error_dialog = None
        self.tray = None

    def do_startup(self) -> None:
        """Called when the application starts; load CSS resources, icon theme paths, and tray."""
        Gtk.Application.do_startup(self)
        self._load_css()
        self._load_icons()
        self._init_tray()

    def do_shutdown(self) -> None:
        """Clean up system tray and background resources on shutdown."""
        if self.tray:
            self.tray.destroy()
            self.tray = None
        Gtk.Application.do_shutdown(self)

    def _init_tray(self) -> None:
        """Initialize the DBus StatusNotifierItem system tray indicator if enabled."""
        settings = self.settings_store.load()
        if settings.get("enable_tray", True):
            try:
                self.tray = CodeWriterTray(
                    on_toggle_window=self._tray_toggle_window,
                    on_arm=self._tray_arm,
                    on_pause_resume=self._tray_pause_resume,
                    on_stop=self._tray_stop,
                    on_simulation_player=self._tray_simulation_player,
                    on_settings=self._tray_settings,
                    on_quit=self._tray_quit,
                )
            except Exception as e:
                logger.warning(f"Could not initialize system tray indicator: {e}")

    def _tray_toggle_window(self) -> None:
        if self.window:
            self.window.toggle_visibility()
        else:
            self._show_main_window()

    def _tray_arm(self) -> None:
        if self.window:
            if not self.window.is_visible():
                self.window.present()
            self.window.arm_simulation()

    def _tray_pause_resume(self) -> None:
        if self.window:
            self.window.pause_or_resume_simulation()

    def _tray_stop(self) -> None:
        if self.window:
            self.window.stop_simulation()

    def _tray_simulation_player(self) -> None:
        if self.window:
            if not self.window.is_visible():
                self.window.present()
            self.window.open_simulation_player()

    def _tray_settings(self) -> None:
        if self.window:
            if not self.window.is_visible():
                self.window.present()
            self.window.open_preferences()

    def _tray_quit(self) -> None:
        self.quit()


    def do_activate(self) -> None:
        """Called on application activation; validates backend availability before showing window."""
        is_ok, reason = self.backend.is_available()
        if not is_ok:
            self._show_error_dialog(reason)
            return

        self._show_main_window()

    def _show_main_window(self) -> None:
        """Instantiate and present the main CodeWriter window with saved settings."""
        if not self.window:
            settings = self.settings_store.load()
            self.window = CodeWriterWindow(
                application=self,
                backend=self.backend,
                settings_store=self.settings_store,
                initial_settings=settings,
            )
            self.window.set_icon_name("codewriter")
        self.window.present()
        if self.tray:
            self.tray.set_window_visible(True)

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
            is_ok, reason = self.backend.is_available(force=True)
            if is_ok:
                dialog.close()
                self.error_dialog = None
                self._show_main_window()
            else:
                dialog.set_reason(reason)
        else:  # Quit or closed
            dialog.close()
            self.quit()

    def _load_icons(self) -> None:
        """Add application resource icons to the GTK Icon Theme."""
        search_dirs = [
            os.path.join(os.path.dirname(__file__), "resources", "icons"),
            os.path.expanduser("~/.local/share/icons/hicolor/scalable/apps"),
            os.path.expanduser("~/.local/share/icons/hicolor"),
            os.path.expanduser("~/.local/share/icons"),
            os.path.expanduser("~/.local/share/pixmaps"),
        ]
        display = Gdk.Display.get_default()
        if display:
            theme = Gtk.IconTheme.get_for_display(display)
            for d in search_dirs:
                if os.path.exists(d):
                    theme.add_search_path(d)
        Gtk.Window.set_default_icon_name("codewriter")

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
    GLib.set_prgname("com.local.codewriter")
    GLib.set_application_name("CodeWriter")
    app = CodeWriterApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())

