"""
Main application window for CodeTyper.
Constructs the GTK4 GUI shell with countdown overlay and state management.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from backend.ydotool import BackendUnavailableError, YdotoolBackend
from core.app_state import AppState
from core.text_processor import preserve, smart
from ui.countdown import CountdownOverlay
from ui.editor import CodeEditor

# Preset delay constants (in milliseconds)
PRESET_FAST_MS = 2
PRESET_NORMAL_MS = 8
PRESET_SAFE_MS = 20


class CodeTyperWindow(Gtk.ApplicationWindow):
    """Main window for CodeTyper."""

    def __init__(self, backend: YdotoolBackend = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.backend = backend or YdotoolBackend()
        self.state = AppState.IDLE

        self.set_title("CodeTyper")
        self.set_default_size(700, 600)

        # Root layout container wrapped in countdown overlay
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_box.add_css_class("main-container")
        self.countdown_overlay = CountdownOverlay(self.main_box)
        self.set_child(self.countdown_overlay)

        # Build UI sections
        self._build_profile_row()
        self.editor = CodeEditor()
        self.main_box.append(self.editor)
        self._build_mode_row()
        self._build_delay_countdown_row()
        self._build_presets_row()
        self._build_action_row()
        self._build_status_row()

    def _build_profile_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add_css_class("profile-row")
        row.append(Gtk.Label(label="Profile:"))
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
        row.append(Gtk.Label(label="Mode:"))

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
        row.append(Gtk.Label(label="Delay:"))

        self.delay_adj = Gtk.Adjustment.new(5.0, 0.0, 200.0, 1.0, 5.0, 0.0)
        self.delay_spin = Gtk.SpinButton(adjustment=self.delay_adj, climb_rate=1.0, digits=0)
        row.append(self.delay_spin)
        row.append(Gtk.Label(label="ms"))

        separator = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_hexpand(True)
        row.append(separator)

        row.append(Gtk.Label(label="Countdown:"))
        self.countdown_adj = Gtk.Adjustment.new(3.0, 0.0, 10.0, 1.0, 1.0, 0.0)
        self.countdown_spin = Gtk.SpinButton(adjustment=self.countdown_adj, climb_rate=1.0, digits=0)
        row.append(self.countdown_spin)
        row.append(Gtk.Label(label="sec"))
        self.main_box.append(row)

    def _build_presets_row(self) -> None:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.add_css_class("preset-row")
        row.append(Gtk.Label(label="Presets:"))

        for label, val in [("Fast", PRESET_FAST_MS), ("Normal", PRESET_NORMAL_MS), ("Safe", PRESET_SAFE_MS)]:
            btn = Gtk.Button(label=f"{label} ({val}ms)")
            btn.connect("clicked", lambda _, v=val: self.delay_spin.set_value(float(v)))
            row.append(btn)
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

    def _set_state(self, new_state: AppState) -> None:
        """Centralized state machine transition updating state and UI sensitivity."""
        self.state = new_state
        is_idle = (new_state == AppState.IDLE)
        for w in (self.arm_button, self.delay_spin, self.countdown_spin,
                  self.mode_smart_radio, self.mode_preserve_radio,
                  self.profile_dropdown, self.save_profile_btn):
            w.set_sensitive(is_idle)
        self.editor.get_view().set_editable(is_idle)

    def _on_save_profile_clicked(self, _button: Gtk.Button) -> None:
        """No-op handler for Save as Profile (Phase 8)."""
        print("[CodeTyper] Save as Profile pressed — profile management is Phase 8")

    def _on_arm_and_type_clicked(self, _button: Gtk.Button) -> None:
        """Initiate countdown prior to typing."""
        if not self.editor.get_text():
            self.set_status("Editor is empty — nothing to type.")
            return

        self._set_state(AppState.COUNTDOWN)
        seconds = int(self.countdown_spin.get_value())
        self.countdown_overlay.start(
            seconds=seconds,
            on_tick=lambda rem: self.set_status(f"Starting in {rem}..."),
            on_complete=self._do_type,
            on_cancel=self._on_countdown_cancelled,
        )

    def _on_countdown_cancelled(self) -> None:
        """Handle user cancellation of countdown."""
        self.set_status("Cancelled.")
        self._set_state(AppState.IDLE)

    def _do_type(self) -> None:
        """
        Transform text and dispatch typing to backend.
        NOTE: Temporary direct blocking call; replaced by async chunking in Phase 5.
        """
        self._set_state(AppState.TYPING)
        raw_text = self.editor.get_text()
        delay_ms = int(self.delay_spin.get_value())
        processed = smart(raw_text) if self.mode_smart_radio.get_active() else preserve(raw_text)

        try:
            self.backend.type_text(processed, delay_ms)
            self.set_status(f"Typed {len(processed)} characters.")
        except BackendUnavailableError as e:
            self.set_status(f"Error: {e}")
        finally:
            self._set_state(AppState.IDLE)

    def set_status(self, text: str) -> None:
        """Update the status label at the bottom of the window."""
        self.status_label.set_text(f"Status: {text}")
