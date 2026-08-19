"""
Main application window for CodeTyper.
Constructs the GTK4 GUI shell matching the specified layout.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from ui.editor import CodeEditor

# Preset delay constants (in milliseconds)
PRESET_FAST_MS = 2
PRESET_NORMAL_MS = 8
PRESET_SAFE_MS = 20


class CodeTyperWindow(Gtk.ApplicationWindow):
    """Main window for CodeTyper."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_title("CodeTyper")
        self.set_default_size(700, 600)

        # Root layout container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_box.add_css_class("main-container")
        self.set_child(self.main_box)

        # 1. Profile selection row
        self._build_profile_row()

        # 2. Code Editor widget
        self.editor = CodeEditor()
        self.main_box.append(self.editor)

        # 3. Mode row (Smart / Preserve)
        self._build_mode_row()

        # 4. Delay & Countdown row
        self._build_delay_countdown_row()

        # 5. Delay preset buttons row
        self._build_presets_row()

        # 6. Primary Action button (ARM & TYPE)
        self._build_action_row()

        # 7. Status bar row
        self._build_status_row()

    def _build_profile_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add_css_class("profile-row")

        label = Gtk.Label(label="Profile:")
        row.append(label)

        self.profile_dropdown = Gtk.DropDown.new_from_strings(["Default"])
        self.profile_dropdown.set_hexpand(True)
        row.append(self.profile_dropdown)

        self.save_profile_btn = Gtk.Button(label="Save as Profile")
        self.save_profile_btn.connect("clicked", self._on_save_profile_clicked)
        row.append(self.save_profile_btn)

        self.main_box.append(row)

    def _build_mode_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("mode-row")

        label = Gtk.Label(label="Mode:")
        row.append(label)

        self.mode_smart_radio = Gtk.CheckButton(label="Smart")
        self.mode_smart_radio.set_active(True)
        row.append(self.mode_smart_radio)

        self.mode_preserve_radio = Gtk.CheckButton(label="Preserve")
        self.mode_preserve_radio.set_group(self.mode_smart_radio)
        row.append(self.mode_preserve_radio)

        self.main_box.append(row)

    def _build_delay_countdown_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.add_css_class("delay-row")

        # Delay spin button (0–200 ms, default 5)
        delay_label = Gtk.Label(label="Delay:")
        row.append(delay_label)

        self.delay_adj = Gtk.Adjustment.new(5.0, 0.0, 200.0, 1.0, 5.0, 0.0)
        self.delay_spin = Gtk.SpinButton(adjustment=self.delay_adj, climb_rate=1.0, digits=0)
        row.append(self.delay_spin)

        ms_label = Gtk.Label(label="ms")
        row.append(ms_label)

        # Spacing separator
        separator = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_hexpand(True)
        row.append(separator)

        # Countdown spin button (0–10 sec, default 3)
        cd_label = Gtk.Label(label="Countdown:")
        row.append(cd_label)

        self.countdown_adj = Gtk.Adjustment.new(3.0, 0.0, 10.0, 1.0, 1.0, 0.0)
        self.countdown_spin = Gtk.SpinButton(adjustment=self.countdown_adj, climb_rate=1.0, digits=0)
        row.append(self.countdown_spin)

        sec_label = Gtk.Label(label="sec")
        row.append(sec_label)

        self.main_box.append(row)

    def _build_presets_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.add_css_class("preset-row")

        label = Gtk.Label(label="Presets:")
        row.append(label)

        fast_btn = Gtk.Button(label=f"Fast ({PRESET_FAST_MS}ms)")
        fast_btn.connect("clicked", lambda _: self._set_delay_preset(PRESET_FAST_MS))
        row.append(fast_btn)

        normal_btn = Gtk.Button(label=f"Normal ({PRESET_NORMAL_MS}ms)")
        normal_btn.connect("clicked", lambda _: self._set_delay_preset(PRESET_NORMAL_MS))
        row.append(normal_btn)

        safe_btn = Gtk.Button(label=f"Safe ({PRESET_SAFE_MS}ms)")
        safe_btn.connect("clicked", lambda _: self._set_delay_preset(PRESET_SAFE_MS))
        row.append(safe_btn)

        self.main_box.append(row)

    def _build_action_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add_css_class("action-row")

        self.arm_button = Gtk.Button(label="ARM & TYPE")
        self.arm_button.set_hexpand(True)
        self.arm_button.add_css_class("suggested-action")
        self.arm_button.add_css_class("arm-button")
        self.arm_button.connect("clicked", self._on_arm_and_type_clicked)
        row.append(self.arm_button)

        self.main_box.append(row)

    def _build_status_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        row.add_css_class("status-row")

        self.status_label = Gtk.Label(label="Status: Ready", halign=Gtk.Align.START)
        self.status_label.set_hexpand(True)
        row.append(self.status_label)

        self.main_box.append(row)

    def _set_delay_preset(self, delay_ms: int) -> None:
        """Update the Delay spin button to the selected preset value."""
        self.delay_spin.set_value(float(delay_ms))

    def _on_save_profile_clicked(self, _button: Gtk.Button) -> None:
        """No-op handler for Save as Profile (Phase 8)."""
        print("[CodeTyper] Save as Profile pressed — profile management is Phase 8")

    def _on_arm_and_type_clicked(self, _button: Gtk.Button) -> None:
        """No-op handler for ARM & TYPE (Phase 4/5)."""
        print("[CodeTyper] ARM & TYPE pressed — not yet implemented (Phase 4/5)")

    def set_status(self, text: str) -> None:
        """Update the status label at the bottom of the window."""
        self.status_label.set_text(f"Status: {text}")
