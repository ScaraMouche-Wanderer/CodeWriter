"""
Dialog components for CodeTyper.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class BackendErrorDialog(Gtk.MessageDialog):
    """
    Modal dialog shown when the ydotool backend isn't available.
    Shows the specific reason string from is_available().
    Has a 'Retry' button that re-runs the check without restarting the app,
    and a 'Quit' button that closes the application cleanly.
    """

    def __init__(self, parent: Gtk.Window = None, reason: str = "") -> None:
        super().__init__(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.NONE,
            text="CodeTyper — Backend Unavailable",
            secondary_text=reason,
        )
        self.add_button("Retry", Gtk.ResponseType.APPLY)
        self.add_button("Quit", Gtk.ResponseType.CLOSE)
        self.set_default_response(Gtk.ResponseType.APPLY)

    def set_reason(self, reason: str) -> None:
        """Update the secondary text displayed in the dialog."""
        self.set_property("secondary-text", reason)
