"""
Dialog components for CodeTyper.
Includes BackendErrorDialog and ProfileNameDialog.
"""

from typing import Optional

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

    def __init__(self, parent: Optional[Gtk.Window] = None, reason: str = "") -> None:
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


class ProfileNameDialog(Gtk.Dialog):
    """
    Modal dialog allowing user to enter or edit a profile name to save.
    """

    def __init__(self, parent: Optional[Gtk.Window] = None, default_name: str = "Default") -> None:
        super().__init__(
            title="Save as Profile",
            transient_for=parent,
            modal=True,
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        content = self.get_content_area()
        content.set_spacing(8)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(16)
        content.set_margin_end(16)

        label = Gtk.Label(label="Profile Name:", halign=Gtk.Align.START)
        content.append(label)

        self.entry = Gtk.Entry()
        self.entry.set_text(default_name)
        self.entry.set_activates_default(True)
        content.append(self.entry)

    def get_profile_name(self) -> str:
        """Return the trimmed profile name from the entry."""
        return self.entry.get_text().strip()
