"""
Dialog components for CodeTyper.
Includes BackendErrorDialog, ProfileNameDialog, ConfirmReplaceDialog,
ConfirmClearDialog, ConfirmDeleteProfileDialog, and DryRunPreviewDialog.
"""

from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, GtkSource

from core.humanizer import estimate_typing_duration


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
            text="CodeWriter — Backend Unavailable",
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


class ConfirmReplaceDialog(Gtk.MessageDialog):
    """
    Confirmation dialog when loading a recent snippet into an editor with existing content.
    """

    def __init__(self, parent: Optional[Gtk.Window] = None) -> None:
        super().__init__(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Replace Editor Content?",
            secondary_text="The editor currently contains text. Replace it with the selected snippet?",
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Replace", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)


class ConfirmClearDialog(Gtk.MessageDialog):
    """
    Confirmation dialog before clearing a non-empty editor buffer.
    """

    def __init__(self, parent: Optional[Gtk.Window] = None) -> None:
        super().__init__(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.NONE,
            text="Clear Editor?",
            secondary_text="Are you sure you want to clear all editor contents?",
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Clear", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)


class ConfirmDeleteProfileDialog(Gtk.MessageDialog):
    """
    Confirmation dialog before deleting a custom profile.
    """

    def __init__(self, profile_name: str, parent: Optional[Gtk.Window] = None) -> None:
        super().__init__(
            transient_for=parent,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.NONE,
            text=f"Delete Profile '{profile_name}'?",
            secondary_text="This action cannot be undone.",
        )
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Delete", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.CANCEL)


class DryRunPreviewDialog(Gtk.Dialog):
    """
    Modal preview dialog analyzing the processed text before transmission.
    Displays estimated duration, effective WPM, character count, and formatted preview.
    """

    def __init__(
        self,
        parent: Optional[Gtk.Window],
        processed_text: str,
        delay_ms: int,
        mode: str,
        language_id: str,
        enable_humanize: bool = False,
    ) -> None:
        super().__init__(
            title="Pre-Flight Typing Preview",
            transient_for=parent,
            modal=True,
        )
        self.set_default_size(520, 420)
        self.add_button("Close", Gtk.ResponseType.CANCEL)
        self.add_button("ARM & TYPE", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        duration_sec, wpm = estimate_typing_duration(processed_text, delay_ms, enable_humanize=enable_humanize)

        content = self.get_content_area()
        content.set_spacing(10)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(16)
        content.set_margin_end(16)

        # ── Statistics Card ──
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, css_classes=["preview-stats-box"])
        stats_box.set_homogeneous(True)

        # Duration
        dur_display = f"{duration_sec:.1f}s" if duration_sec >= 1 else f"{int(duration_sec*1000)}ms"
        dur_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        dur_col.append(Gtk.Label(label="Est. Duration", css_classes=["preview-stat-label"]))
        dur_col.append(Gtk.Label(label=dur_display, css_classes=["preview-stat-value", "preview-stat-accent"]))
        stats_box.append(dur_col)

        # Speed / WPM
        wpm_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        wpm_col.append(Gtk.Label(label="Est. Speed", css_classes=["preview-stat-label"]))
        wpm_col.append(Gtk.Label(label=f"~{wpm} WPM", css_classes=["preview-stat-value"]))
        stats_box.append(wpm_col)

        # Characters & Lines
        char_count = len(processed_text)
        line_count = len(processed_text.splitlines()) if char_count > 0 else 0
        len_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        len_col.append(Gtk.Label(label="Volume", css_classes=["preview-stat-label"]))
        len_col.append(Gtk.Label(label=f"{char_count} chars · {line_count} lines", css_classes=["preview-stat-value"]))
        stats_box.append(len_col)

        # Mode & Timing Cadence
        cadence_str = "Humanized 🎲" if enable_humanize else "Fixed ⚡"
        mode_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        mode_col.append(Gtk.Label(label="Configuration", css_classes=["preview-stat-label"]))
        mode_col.append(Gtk.Label(label=f"{mode.capitalize()} · {delay_ms}ms · {cadence_str}", css_classes=["preview-stat-value"]))
        stats_box.append(mode_col)

        content.append(stats_box)

        # ── Processed Text Preview ──
        preview_label = Gtk.Label(label="Processed Payload Preview:", halign=Gtk.Align.START, css_classes=["preview-header-label"])
        content.append(preview_label)

        buffer = GtkSource.Buffer()
        buffer.set_text(processed_text)
        if language_id and language_id != "plain":
            lm = GtkSource.LanguageManager.get_default()
            lang = lm.get_language(language_id)
            buffer.set_language(lang)
            buffer.set_highlight_syntax(True)

        view = GtkSource.View.new_with_buffer(buffer)
        view.set_editable(False)
        view.set_show_line_numbers(True)
        view.set_monospace(True)
        view.add_css_class("code-editor-view")

        scroll = Gtk.ScrolledWindow(child=view, hexpand=True, vexpand=True, css_classes=["editor-container"])
        scroll.set_min_content_height(180)
        content.append(scroll)


class SimulationPlayerDialog(Gtk.Dialog):
    """
    Interactive Real-Time Typing Simulation Player and Visualizer.
    Plays back the typing process in an animated canvas with speed controls,
    progress indicators, WPM metrics, and instant ARM & TYPE capability.
    """

    def __init__(
        self,
        parent: Optional[Gtk.Window],
        text: str,
        delay_ms: int,
        language_id: str = "plain",
        enable_humanize: bool = False,
        typo_rate_pct: float = 0.0,
    ) -> None:
        super().__init__(
            title="Live Typing Simulation Player",
            transient_for=parent,
            modal=True,
        )
        self.set_default_size(620, 520)
        self.add_button("Close", Gtk.ResponseType.CANCEL)
        self.add_button("⚡ ARM & TYPE NOW", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self._full_text = text
        self._delay_ms = max(1, delay_ms)
        self._enable_humanize = enable_humanize
        self._typo_rate_pct = typo_rate_pct
        self._speed_multiplier = 1.0

        self._char_index = 0
        self._timer_id: Optional[int] = None
        self._is_playing = False
        self._start_time = 0.0

        content = self.get_content_area()
        content.set_spacing(10)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(16)
        content.set_margin_end(16)

        # ── 1. Top Metrics Bar ──
        stats_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, css_classes=["preview-stats-box"])
        stats_box.set_homogeneous(True)

        self.wpm_label = Gtk.Label(label="0 WPM", css_classes=["preview-stat-value", "preview-stat-accent"])
        wpm_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        wpm_col.append(Gtk.Label(label="Live Speed", css_classes=["preview-stat-label"]))
        wpm_col.append(self.wpm_label)
        stats_box.append(wpm_col)

        self.progress_count_label = Gtk.Label(label=f"0 / {len(text)} chars", css_classes=["preview-stat-value"])
        count_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        count_col.append(Gtk.Label(label="Progress", css_classes=["preview-stat-label"]))
        count_col.append(self.progress_count_label)
        stats_box.append(count_col)

        mode_desc = f"{delay_ms}ms" + (" · Humanized 🎲" if enable_humanize else " · Fixed ⚡")
        cfg_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        cfg_col.append(Gtk.Label(label="Base Engine", css_classes=["preview-stat-label"]))
        cfg_col.append(Gtk.Label(label=mode_desc, css_classes=["preview-stat-value"]))
        stats_box.append(cfg_col)

        content.append(stats_box)

        # ── 2. Animated Simulation Screen ──
        self.sim_buffer = GtkSource.Buffer()
        if language_id and language_id != "plain":
            lm = GtkSource.LanguageManager.get_default()
            lang = lm.get_language(language_id)
            self.sim_buffer.set_language(lang)
            self.sim_buffer.set_highlight_syntax(True)

        self.sim_view = GtkSource.View.new_with_buffer(self.sim_buffer)
        self.sim_view.set_editable(False)
        self.sim_view.set_show_line_numbers(True)
        self.sim_view.set_monospace(True)
        self.sim_view.set_highlight_current_line(True)
        self.sim_view.add_css_class("code-editor-view")

        scroll = Gtk.ScrolledWindow(child=self.sim_view, hexpand=True, vexpand=True, css_classes=["editor-container"])
        scroll.set_min_content_height(240)
        content.append(scroll)

        # ── 3. Live Progress Bar ──
        self.progress_bar = Gtk.ProgressBar(show_text=True, text="0%")
        self.progress_bar.add_css_class("codewriter-progress")
        content.append(self.progress_bar)

        # ── 4. Playback Controls Toolbar ──
        ctrl_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.play_btn = Gtk.Button(css_classes=["suggested-action", "toolbar-btn"])
        self.play_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.play_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        self.play_label = Gtk.Label(label="Play Simulation")
        self.play_box.append(self.play_icon)
        self.play_box.append(self.play_label)
        self.play_btn.set_child(self.play_box)
        self.play_btn.connect("clicked", self._on_play_pause_clicked)
        ctrl_bar.append(self.play_btn)

        self.restart_btn = Gtk.Button(css_classes=["toolbar-btn"])
        restart_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        restart_box.append(Gtk.Image.new_from_icon_name("view-refresh-symbolic"))
        restart_box.append(Gtk.Label(label="Restart"))
        self.restart_btn.set_child(restart_box)
        self.restart_btn.connect("clicked", self._on_restart_clicked)
        ctrl_bar.append(self.restart_btn)

        ctrl_bar.append(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True))

        # Speed Multiplier
        speed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        speed_box.append(Gtk.Label(label="Playback Speed:", css_classes=["toolbar-label"]))
        self.speed_dropdown = Gtk.DropDown.new_from_strings([
            "0.5x (Slow)", "1.0x (Real-time)", "2.0x (Fast)", "5.0x (Blitz)", "10.0x (Instant)"
        ])
        self.speed_dropdown.set_selected(1)  # Default 1.0x
        self.speed_dropdown.connect("notify::selected", self._on_speed_changed)
        speed_box.append(self.speed_dropdown)
        ctrl_bar.append(speed_box)

        content.append(ctrl_bar)
        self.connect("response", self._on_dialog_response)

    def _on_speed_changed(self, dropdown, _param) -> None:
        speeds = [0.5, 1.0, 2.0, 5.0, 10.0]
        idx = dropdown.get_selected()
        if 0 <= idx < len(speeds):
            self._speed_multiplier = speeds[idx]

    def _on_play_pause_clicked(self, _btn) -> None:
        if self._is_playing:
            self._pause()
        else:
            self._play()

    def _play(self) -> None:
        if self._char_index >= len(self._full_text):
            self._char_index = 0
            self.sim_buffer.set_text("")

        self._is_playing = True
        import time
        if self._start_time == 0.0:
            self._start_time = time.monotonic()
        self.play_icon.set_from_icon_name("media-playback-pause-symbolic")
        self.play_label.set_text("Pause")
        self._schedule_next_char()

    def _pause(self) -> None:
        self._is_playing = False
        if self._timer_id:
            from gi.repository import GLib
            GLib.source_remove(self._timer_id)
            self._timer_id = None
        self.play_icon.set_from_icon_name("media-playback-start-symbolic")
        self.play_label.set_text("Resume")

    def _on_restart_clicked(self, _btn) -> None:
        self._pause()
        self._char_index = 0
        self._start_time = 0.0
        self.sim_buffer.set_text("")
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("0%")
        self.progress_count_label.set_text(f"0 / {len(self._full_text)} chars")
        self.wpm_label.set_text("0 WPM")
        self.play_label.set_text("Play Simulation")

    def _schedule_next_char(self) -> None:
        if not self._is_playing or self._char_index >= len(self._full_text):
            if self._char_index >= len(self._full_text):
                self._pause()
                self.play_label.set_text("Replay")
            return

        from core.humanizer import calculate_char_delay
        char = self._full_text[self._char_index]
        prev_char = self._full_text[self._char_index - 1] if self._char_index > 0 else ""

        delay_sec = calculate_char_delay(
            char=char,
            prev_char=prev_char,
            base_delay_ms=self._delay_ms,
            enable_humanize=self._enable_humanize,
        )

        effective_delay_ms = max(1, int((delay_sec * 1000) / self._speed_multiplier))
        from gi.repository import GLib
        self._timer_id = GLib.timeout_add(effective_delay_ms, self._on_step)

    def _on_step(self) -> bool:
        if not self._is_playing:
            return False

        if self._char_index < len(self._full_text):
            char = self._full_text[self._char_index]
            self.sim_buffer.insert_at_cursor(char)
            self._char_index += 1

            total = len(self._full_text)
            fraction = self._char_index / total if total > 0 else 1.0
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f"{int(fraction * 100)}%")
            self.progress_count_label.set_text(f"{self._char_index} / {total} chars")

            # Update live WPM
            import time
            elapsed = time.monotonic() - self._start_time
            if elapsed > 0:
                mins = elapsed / 60.0
                live_wpm = int((self._char_index / 5.0) / mins * self._speed_multiplier)
                self.wpm_label.set_text(f"{live_wpm} WPM")

            self._schedule_next_char()
        else:
            self._pause()
            self.play_label.set_text("Replay")

        return False

    def _on_dialog_response(self, _dialog, _response) -> None:
        self._pause()


class PreferencesDialog(Gtk.Dialog):
    """
    Comprehensive Preferences and Configuration Dialog for CodeWriter.
    Manages Typing Engine, Humanizer, System Tray, Desktop, and Editor options.
    """

    def __init__(
        self,
        parent: Optional[Gtk.Window],
        settings: dict,
        on_save: Optional[callable] = None,
    ) -> None:
        super().__init__(
            title="CodeWriter Preferences",
            transient_for=parent,
            modal=True,
        )
        self.set_default_size(540, 460)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save Preferences", Gtk.ResponseType.OK)
        self.set_default_response(Gtk.ResponseType.OK)

        self._settings = dict(settings)
        self._on_save = on_save

        content = self.get_content_area()
        content.set_spacing(12)
        content.set_margin_top(14)
        content.set_margin_bottom(14)
        content.set_margin_start(18)
        content.set_margin_end(18)

        # ── Tabs / Stack ──
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)
        switcher.set_halign(Gtk.Align.CENTER)
        content.append(switcher)

        # Tab 1: Typing Engine
        engine_box = self._build_engine_tab()
        stack.add_titled(engine_box, "engine", "Typing Engine")

        # Tab 2: Humanizer
        human_box = self._build_humanizer_tab()
        stack.add_titled(human_box, "humanizer", "Humanizer & Typos")

        # Tab 3: System Tray & Desktop
        tray_box = self._build_tray_tab()
        stack.add_titled(tray_box, "tray", "Desktop & Tray")

        # Tab 4: Editor Display
        editor_box = self._build_editor_tab()
        stack.add_titled(editor_box, "editor", "Editor Display")

        content.append(stack)

    def _build_engine_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=10)

        # Delay
        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row1.append(Gtk.Label(label="Default Key Delay (ms):", halign=Gtk.Align.START, hexpand=True))
        self.delay_spin = Gtk.SpinButton.new_with_range(1, 1000, 1)
        self.delay_spin.set_value(self._settings.get("default_delay_ms", 15))
        row1.append(self.delay_spin)
        box.append(row1)

        # Countdown
        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row2.append(Gtk.Label(label="Default Countdown Timer (sec):", halign=Gtk.Align.START, hexpand=True))
        self.countdown_spin = Gtk.SpinButton.new_with_range(0, 30, 1)
        self.countdown_spin.set_value(self._settings.get("default_countdown_sec", 3))
        row2.append(self.countdown_spin)
        box.append(row2)

        # Default Mode
        row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row3.append(Gtk.Label(label="Default Text Mode:", halign=Gtk.Align.START, hexpand=True))
        self.mode_dropdown = Gtk.DropDown.new_from_strings(["Smart Auto-Indent", "Preserve Raw", "Strip Line Numbers"])
        mode_str = self._settings.get("default_mode", "smart")
        mode_idx = 1 if mode_str == "preserve" else (2 if mode_str == "strip" else 0)
        self.mode_dropdown.set_selected(mode_idx)
        row3.append(self.mode_dropdown)
        box.append(row3)

        # Auto-Close Brackets Compensate
        row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row4.append(Gtk.Label(label="Compensate IDE Auto-Close Brackets:", halign=Gtk.Align.START, hexpand=True))
        self.auto_close_switch = Gtk.Switch(active=self._settings.get("auto_close_compensate", False))
        row4.append(self.auto_close_switch)
        box.append(row4)

        return box

    def _build_humanizer_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=10)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row1.append(Gtk.Label(label="Enable Humanized Cadence by Default:", halign=Gtk.Align.START, hexpand=True))
        self.humanize_switch = Gtk.Switch(active=self._settings.get("humanize_cadence", False))
        row1.append(self.humanize_switch)
        box.append(row1)

        row2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        row2.append(Gtk.Label(label="Default Typo Simulation Error Rate (%):", halign=Gtk.Align.START))
        self.typo_spin = Gtk.SpinButton.new_with_range(0, 10, 0.5)
        self.typo_spin.set_value(self._settings.get("typo_rate", 0))
        row2.append(self.typo_spin)
        box.append(row2)

        return box

    def _build_tray_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=10)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row1.append(Gtk.Label(label="Enable System Tray Status Indicator:", halign=Gtk.Align.START, hexpand=True))
        self.tray_switch = Gtk.Switch(active=self._settings.get("enable_tray", True))
        row1.append(self.tray_switch)
        box.append(row1)

        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row2.append(Gtk.Label(label="Minimize to System Tray on Window Close:", halign=Gtk.Align.START, hexpand=True))
        self.min_tray_switch = Gtk.Switch(active=self._settings.get("minimize_to_tray", False))
        row2.append(self.min_tray_switch)
        box.append(row2)

        row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row3.append(Gtk.Label(label="Send Desktop Notification on Completion:", halign=Gtk.Align.START, hexpand=True))
        self.notif_switch = Gtk.Switch(active=self._settings.get("notify_on_complete", True))
        row3.append(self.notif_switch)
        box.append(row3)

        row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row4.append(Gtk.Label(label="Play Acoustic Bell Chime on Finish:", halign=Gtk.Align.START, hexpand=True))
        self.sound_switch = Gtk.Switch(active=self._settings.get("sound_chime", True))
        row4.append(self.sound_switch)
        box.append(row4)

        return box

    def _build_editor_tab(self) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=10)

        row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row1.append(Gtk.Label(label="Editor Font Size (pt):", halign=Gtk.Align.START, hexpand=True))
        self.font_spin = Gtk.SpinButton.new_with_range(8, 32, 1)
        self.font_spin.set_value(self._settings.get("font_size", 11))
        row1.append(self.font_spin)
        box.append(row1)

        row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row2.append(Gtk.Label(label="Show Line Numbers Gutter:", halign=Gtk.Align.START, hexpand=True))
        self.line_num_switch = Gtk.Switch(active=self._settings.get("show_line_numbers", True))
        row2.append(self.line_num_switch)
        box.append(row2)

        row3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row3.append(Gtk.Label(label="Soft Word Wrap:", halign=Gtk.Align.START, hexpand=True))
        self.word_wrap_switch = Gtk.Switch(active=self._settings.get("word_wrap", False))
        row3.append(self.word_wrap_switch)
        box.append(row3)

        row4 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row4.append(Gtk.Label(label="Highlight Current Line:", halign=Gtk.Align.START, hexpand=True))
        self.highlight_line_switch = Gtk.Switch(active=self._settings.get("highlight_current_line", True))
        row4.append(self.highlight_line_switch)
        box.append(row4)

        return box

    def get_updated_settings(self) -> dict:
        """Return the dictionary of updated settings from the dialog inputs."""
        mode_options = ["smart", "preserve", "strip"]
        selected_mode = mode_options[self.mode_dropdown.get_selected()]

        return {
            "default_delay_ms": int(self.delay_spin.get_value()),
            "default_countdown_sec": int(self.countdown_spin.get_value()),
            "default_mode": selected_mode,
            "auto_close_compensate": self.auto_close_switch.get_active(),
            "humanize_cadence": self.humanize_switch.get_active(),
            "typo_rate": float(self.typo_spin.get_value()),
            "enable_tray": self.tray_switch.get_active(),
            "minimize_to_tray": self.min_tray_switch.get_active(),
            "notify_on_complete": self.notif_switch.get_active(),
            "sound_chime": self.sound_switch.get_active(),
            "font_size": int(self.font_spin.get_value()),
            "show_line_numbers": self.line_num_switch.get_active(),
            "word_wrap": self.word_wrap_switch.get_active(),
            "highlight_current_line": self.highlight_line_switch.get_active(),
        }

