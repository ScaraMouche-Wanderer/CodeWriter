"""
Main application window for CodeWriter.
Constructs the GTK4 GUI shell with:
- Crisp vector HD symbolic icons across all toolbars, popovers, and controls
- Auto-adjustable responsive layout (split-window and narrow screens)
- Multi-tab editor with drag-and-drop file loading
- Find & Replace bar
- Countdown overlay & background typing engine
- Human-like typing simulation & jitter cadence
- AI Markdown code block cleaner & code transforms
- Starter language templates & boilerplates
- Dry-run pre-flight typing preview modal
- Session log with WPM stats, analytics summary, and CSV export
- Profile persistence & recent snippets history in dedicated popover
- Desktop notifications on completion
- Comprehensive keyboard shortcuts
"""

import os
import time
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango

from backend.ydotool import YdotoolBackend
from core.app_state import AppState
from core.code_tools import (
    analyze_code_stats,
    change_case,
    convert_spaces_to_tabs,
    convert_tabs_to_spaces,
    decode_base64,
    decode_url,
    deduplicate_lines,
    encode_base64,
    encode_url,
    escape_string,
    extract_markdown_code,
    format_html,
    format_json,
    format_sql,
    minify_json,
    remove_blank_lines,
    sort_lines,
    strip_comments_and_docstrings,
    trim_trailing_whitespace,
    unescape_string,
)

from core.humanizer import estimate_typing_duration
from core.profiles import ProfileStore
from core.session_log import SessionLogStore
from core.settings import SettingsStore
from core.snippets import SnippetStore
from core.sound import play_chime, play_tick
from core.templates import STARTER_TEMPLATES, CodeTemplate
from core.text_processor import compensate_auto_close, preserve, smart, strip_line_numbers
from core.typing_engine import TypingController
from ui.countdown import CountdownOverlay
from ui.dialogs import (
    ConfirmClearDialog,
    ConfirmDeleteProfileDialog,
    ConfirmReplaceDialog,
    DryRunPreviewDialog,
    PreferencesDialog,
    ProfileNameDialog,
    SimulationPlayerDialog,
)
from ui.editor import SUPPORTED_LANGUAGES, CodeEditor, detect_language_from_path
from ui.find_bar import FindBar
from ui.shortcuts import create_shortcuts_window
from ui.tab_manager import TabManager


PRESET_FAST_MS, PRESET_NORMAL_MS, PRESET_SAFE_MS = 2, 8, 20


def _create_menu_row(
    icon_name: str,
    label_text: str,
    shortcut_text: str = "",
    is_highlight: bool = False,
) -> Gtk.Button:
    """Create a sleek popover menu button with HD vector icon, left text, and shortcut badge."""
    btn = Gtk.Button(css_classes=["popover-menu-item"] + (["popover-menu-item-accent"] if is_highlight else []))
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

    icon = Gtk.Image.new_from_icon_name(icon_name)
    icon.set_icon_size(Gtk.IconSize.NORMAL)
    icon.add_css_class("menu-icon")
    box.append(icon)

    label = Gtk.Label(label=label_text, halign=Gtk.Align.START, hexpand=True, css_classes=["popover-item-text"])
    box.append(label)

    if shortcut_text:
        shortcut = Gtk.Label(label=shortcut_text, halign=Gtk.Align.END, css_classes=["popover-item-shortcut"])
        box.append(shortcut)

    btn.set_child(box)
    return btn


class CodeWriterWindow(Gtk.ApplicationWindow):
    """Main window for CodeWriter."""

    def __init__(
        self,
        backend: Optional[YdotoolBackend] = None,
        settings_store: Optional[SettingsStore] = None,
        initial_settings: Optional[dict] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.backend = backend or YdotoolBackend()
        self.settings_store = settings_store or SettingsStore()
        self.typing_controller = TypingController(self.backend)
        self.profile_store = ProfileStore()
        self.snippet_store = SnippetStore()
        self.session_log_store = SessionLogStore()
        self._profiles = self.profile_store.load()
        self._recent_snippets = self.snippet_store.load()
        self._session_logs = self.session_log_store.load()
        self.state = AppState.IDLE
        self._active_target_text: str = ""
        self._is_typing_selection: bool = False
        self._typing_start_time: float = 0.0

        settings = initial_settings or self.settings_store.load()
        self._notify_on_complete = settings.get("notify_on_complete", True)
        self._initial_humanize = settings.get("humanize_cadence", False)
        self._typo_rate = settings.get("typo_rate", 0)
        self._auto_close = settings.get("auto_close_compensate", False)
        self._enable_tray = settings.get("enable_tray", True)
        self._minimize_to_tray = settings.get("minimize_to_tray", False)
        self._sound_chime = settings.get("sound_chime", True)

        self.set_title("CodeWriter")
        self.set_icon_name("codewriter")
        self.set_size_request(400, 360)
        self.set_default_size(settings.get("window_width", 780), settings.get("window_height", 580))

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, css_classes=["main-container"])
        self.countdown_overlay = CountdownOverlay(self.main_box)
        self.set_child(self.countdown_overlay)

        self._build_ui()
        self._populate_profiles_dropdown(selected_name=settings.get("last_selected_profile", "Default"))
        self._refresh_recent_snippets()
        self._refresh_session_logs()
        self._update_editor_stats()

        # Apply initial editor configuration
        self._apply_preferences_update(settings)


        self.profile_dropdown.connect("notify::selected", self._on_profile_selected)
        self.connect("close-request", self._on_close_request)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)


    def _create_icon_button(
        self, icon_name: str, label_text: Optional[str] = None, tooltip: str = "", css_classes: Optional[list] = None
    ) -> Gtk.Button:
        """Create a toolbar button with an HD symbolic icon and optional label."""
        btn = Gtk.Button(css_classes=css_classes or ["toolbar-btn"])
        if tooltip:
            btn.set_tooltip_text(tooltip)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        box.append(icon)
        if label_text:
            box.append(Gtk.Label(label=label_text))
        btn.set_child(box)
        return btn

    def _create_icon_menubutton(
        self, icon_name: str, label_text: Optional[str] = None, tooltip: str = "", css_classes: Optional[list] = None
    ) -> Gtk.MenuButton:
        """Create a toolbar menubutton with an HD symbolic icon and optional label."""
        btn = Gtk.MenuButton(css_classes=css_classes or ["toolbar-btn"])
        if tooltip:
            btn.set_tooltip_text(tooltip)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        box.append(icon)
        if label_text:
            box.append(Gtk.Label(label=label_text))
        btn.set_child(box)
        return btn

    # ═══════════════════════════════════════════════════════
    #  BUILD UI (RESPONSIVE AUTO-ADJUSTING SECTIONS)
    # ═══════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        # ── 1. Top App Toolbar (Profile + Popovers + Shortcuts) ──
        app_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, css_classes=["top-toolbar"])

        # Profile Section (Left)
        profile_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["toolbar-group"])
        profile_label = Gtk.Label(label="Profile:", css_classes=["toolbar-label"])
        self.profile_dropdown = Gtk.DropDown(css_classes=["profile-dropdown"])

        self.save_profile_btn = self._create_icon_button("document-save-symbolic", "Save", "Save Profile")
        self.save_profile_btn.connect("clicked", self._on_save_profile_clicked)

        self.delete_profile_btn = self._create_icon_button(
            "user-trash-symbolic", "Delete", "Delete Profile", css_classes=["toolbar-btn", "toolbar-btn-danger"]
        )
        self.delete_profile_btn.set_sensitive(False)
        self.delete_profile_btn.connect("clicked", self._on_delete_profile_clicked)

        profile_actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["linked"])
        profile_actions.append(self.save_profile_btn)
        profile_actions.append(self.delete_profile_btn)

        profile_group.append(profile_label)
        profile_group.append(self.profile_dropdown)
        profile_group.append(profile_actions)
        app_toolbar.append(profile_group)

        # Flexible Spacer
        app_toolbar.append(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True))

        # Utilities / Popovers (Right)
        util_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["linked"])

        self.history_btn = self._create_icon_menubutton("document-open-recent-symbolic", "History", "Recent Snippets")
        self._build_history_popover()
        util_group.append(self.history_btn)

        self.sessions_btn = self._create_icon_menubutton("utilities-system-monitor-symbolic", "Logs", "Session Statistics")
        self._build_sessions_popover()
        util_group.append(self.sessions_btn)

        self.shortcuts_btn = self._create_icon_button("input-keyboard-symbolic", None, "Keyboard Shortcuts (Ctrl+?)")
        self.shortcuts_btn.connect("clicked", self._on_show_shortcuts)
        util_group.append(self.shortcuts_btn)

        self.pref_btn = self._create_icon_button("emblem-system-symbolic", None, "Preferences (Ctrl+,)")
        self.pref_btn.connect("clicked", lambda _: self._show_preferences_dialog())
        util_group.append(self.pref_btn)
        app_toolbar.append(util_group)



        # ── 2. Editor Toolbar (Language + Tools + Templates + File Actions) ──
        editor_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, css_classes=["editor-toolbar-row"])

        # Language selection
        lang_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["toolbar-group"])
        lang_label = Gtk.Label(label="Lang:", css_classes=["toolbar-label"])
        lang_names = [label for label, _ in SUPPORTED_LANGUAGES]
        self.language_dropdown = Gtk.DropDown.new_from_strings(lang_names)
        self.language_dropdown.add_css_class("lang-dropdown")
        self.language_dropdown.connect("notify::selected", self._on_language_selected)
        lang_group.append(lang_label)
        lang_group.append(self.language_dropdown)

        # Templates & Tools popover buttons
        feature_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["linked"])

        self.tools_btn = self._create_icon_menubutton(
            "preferences-other-symbolic", "Tools", "Code tools, AI Markdown extract, and dry-run preview"
        )
        self._build_tools_popover()
        feature_group.append(self.tools_btn)

        self.templates_btn = self._create_icon_menubutton(
            "text-x-generic-symbolic", "Templates", "Starter boilerplates for competitive programming"
        )
        self._build_templates_popover()
        feature_group.append(self.templates_btn)

        lang_group.append(feature_group)
        editor_toolbar.append(lang_group)

        # Flexible Spacer
        editor_toolbar.append(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True))

        # File Operations (Open, Save, Paste, Copy, Clear)
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["linked"])
        self.open_btn = self._create_icon_button("document-open-symbolic", "Open", "Open File (Ctrl+O)")
        self.open_btn.connect("clicked", self._on_open_file_clicked)
        file_group.append(self.open_btn)

        self.save_btn = self._create_icon_button("document-save-symbolic", "Save", "Save File (Ctrl+S)")
        self.save_btn.connect("clicked", self._on_save_file_clicked)
        file_group.append(self.save_btn)

        self.paste_btn = self._create_icon_button("edit-paste-symbolic", "Paste", "Paste Clipboard")
        self.paste_btn.connect("clicked", lambda _: self._active_editor().paste_clipboard())
        file_group.append(self.paste_btn)

        self.copy_btn = self._create_icon_button("edit-copy-symbolic", "Copy", "Copy Selection / All")
        self.copy_btn.connect("clicked", lambda _: self._active_editor().copy_clipboard())
        file_group.append(self.copy_btn)

        self.clear_btn = self._create_icon_button("edit-clear-symbolic", "Clear", "Clear Editor (Ctrl+L)")
        self.clear_btn.connect("clicked", self._on_clear_clicked)
        file_group.append(self.clear_btn)
        editor_toolbar.append(file_group)

        # ── 3. Tab Manager & Editor Canvas ──
        self.tab_manager = TabManager()
        self.tab_manager.set_on_tab_changed(self._on_tab_changed)
        self._setup_editor_listeners(self._active_editor())

        # ── 4. Find & Replace Bar ──
        self.find_bar = FindBar(self._active_editor().get_buffer())

        # ── 5. Compact Control Deck (Auto-wrapping 2-row layout) ──
        control_deck = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, css_classes=["control-deck"])

        # Row A: Mode selection (Left) + Wait Countdown (Right)
        deck_row1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, css_classes=["deck-subrow"])

        mode_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["toolbar-group"])
        mode_label = Gtk.Label(label="Mode:", css_classes=["control-label"])
        mode_pills = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2, css_classes=["mode-segmented"])

        self.mode_smart_radio = Gtk.CheckButton(label="Smart", active=True, css_classes=["segmented-pill"])
        self.mode_smart_radio.set_tooltip_text("Auto-indent: Strips leading whitespace per line")
        self.mode_preserve_radio = Gtk.CheckButton(label="Preserve", group=self.mode_smart_radio, css_classes=["segmented-pill"])
        self.mode_preserve_radio.set_tooltip_text("Verbatim: Exact whitespace preserved")
        self.mode_strip_radio = Gtk.CheckButton(label="Strip Lines", group=self.mode_smart_radio, css_classes=["segmented-pill"])
        self.mode_strip_radio.set_tooltip_text("Strip line numbers (1: , 1. , 1 | )")

        mode_pills.append(self.mode_smart_radio)
        mode_pills.append(self.mode_preserve_radio)
        mode_pills.append(self.mode_strip_radio)
        mode_group.append(mode_label)
        mode_group.append(mode_pills)
        deck_row1.append(mode_group)

        deck_row1.append(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True))

        countdown_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["toolbar-group"])
        cd_label = Gtk.Label(label="Wait:", css_classes=["control-label"])
        self.countdown_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment.new(3.0, 0.0, 10.0, 1.0, 1.0, 0.0), digits=0, css_classes=["compact-spin"])
        self.countdown_spin.set_tooltip_text("Countdown before typing (sec)")
        countdown_group.append(cd_label)
        countdown_group.append(self.countdown_spin)
        countdown_group.append(Gtk.Label(label="s", css_classes=["unit-label"]))
        deck_row1.append(countdown_group)

        control_deck.append(deck_row1)

        # Row B: Speed Presets + Humanize toggle (Left) + Custom Delay (Right)
        deck_row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, css_classes=["deck-subrow"])

        speed_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["toolbar-group"])
        speed_label = Gtk.Label(label="Speed:", css_classes=["control-label"])
        presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["linked"])

        self.preset_fast_btn = Gtk.Button(label=f"Fast ({PRESET_FAST_MS}ms)", css_classes=["preset-btn"])
        self.preset_fast_btn.connect("clicked", lambda _: self.delay_spin.set_value(float(PRESET_FAST_MS)))
        self.preset_normal_btn = Gtk.Button(label=f"Normal ({PRESET_NORMAL_MS}ms)", css_classes=["preset-btn"])
        self.preset_normal_btn.connect("clicked", lambda _: self.delay_spin.set_value(float(PRESET_NORMAL_MS)))
        self.preset_safe_btn = Gtk.Button(label=f"Safe ({PRESET_SAFE_MS}ms)", css_classes=["preset-btn"])
        self.preset_safe_btn.connect("clicked", lambda _: self.delay_spin.set_value(float(PRESET_SAFE_MS)))

        self.humanize_toggle = Gtk.ToggleButton(active=self._initial_humanize, css_classes=["preset-btn"])
        self.humanize_toggle.set_tooltip_text("Simulate natural human keystroke jitter and delimiter pauses")
        human_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        human_icon = Gtk.Image.new_from_icon_name("starred-symbolic")
        human_icon.set_icon_size(Gtk.IconSize.NORMAL)
        human_box.append(human_icon)
        human_box.append(Gtk.Label(label="Human"))
        self.humanize_toggle.set_child(human_box)

        presets_box.append(self.preset_fast_btn)
        presets_box.append(self.preset_normal_btn)
        presets_box.append(self.preset_safe_btn)
        presets_box.append(self.humanize_toggle)
        speed_group.append(speed_label)
        speed_group.append(presets_box)
        deck_row2.append(speed_group)

        deck_row2.append(Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True))

        delay_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["toolbar-group"])
        delay_label = Gtk.Label(label="Delay:", css_classes=["control-label"])
        self.delay_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment.new(5.0, 0.0, 200.0, 1.0, 5.0, 0.0), digits=0, css_classes=["compact-spin"])
        self.delay_spin.set_tooltip_text("Keystroke delay (ms)")
        delay_group.append(delay_label)
        delay_group.append(self.delay_spin)
        delay_group.append(Gtk.Label(label="ms", css_classes=["unit-label"]))
        deck_row2.append(delay_group)

        control_deck.append(deck_row2)

        # ── 6. Action Row (ARM & TYPE, PAUSE, RESUME, STOP) ──
        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, css_classes=["action-row"])

        self.arm_button = Gtk.Button(hexpand=True, css_classes=["suggested-action", "arm-button"])
        arm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.CENTER)
        arm_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        arm_icon.set_icon_size(Gtk.IconSize.NORMAL)
        self.arm_button_label = Gtk.Label(label="ARM & TYPE (Ctrl+Enter)")
        arm_box.append(arm_icon)
        arm_box.append(self.arm_button_label)
        self.arm_button.set_child(arm_box)
        self.arm_button.connect("clicked", self._on_arm_and_type_clicked)

        self.pause_button = Gtk.Button(hexpand=True, visible=False, css_classes=["pause-button"])
        pause_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.CENTER)
        pause_icon = Gtk.Image.new_from_icon_name("media-playback-pause-symbolic")
        pause_icon.set_icon_size(Gtk.IconSize.NORMAL)
        pause_box.append(pause_icon)
        pause_box.append(Gtk.Label(label="PAUSE (Space)"))
        self.pause_button.set_child(pause_box)
        self.pause_button.connect("clicked", self._on_pause_clicked)

        self.resume_button = Gtk.Button(hexpand=True, visible=False, css_classes=["resume-button"])
        resume_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.CENTER)
        resume_icon = Gtk.Image.new_from_icon_name("media-playback-start-symbolic")
        resume_icon.set_icon_size(Gtk.IconSize.NORMAL)
        resume_box.append(resume_icon)
        resume_box.append(Gtk.Label(label="RESUME (Space)"))
        self.resume_button.set_child(resume_box)
        self.resume_button.connect("clicked", self._on_resume_clicked)

        self.stop_button = Gtk.Button(hexpand=False, visible=False, css_classes=["destructive-action", "stop-button"])
        stop_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, halign=Gtk.Align.CENTER)
        stop_icon = Gtk.Image.new_from_icon_name("media-playback-stop-symbolic")
        stop_icon.set_icon_size(Gtk.IconSize.NORMAL)
        stop_box.append(stop_icon)
        stop_box.append(Gtk.Label(label="STOP (Esc)"))
        self.stop_button.set_child(stop_box)
        self.stop_button.connect("clicked", self._on_stop_clicked)

        action_row.append(self.arm_button)
        action_row.append(self.pause_button)
        action_row.append(self.resume_button)
        action_row.append(self.stop_button)

        # ── 7. Progress Bar ──
        self.progress_bar = Gtk.ProgressBar(visible=False, css_classes=["codewriter-progress", "codetyper-progress"])

        # ── 8. Unified Status & Telemetry Footer ──
        footer_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, css_classes=["status-footer-row"])

        self.status_pill = Gtk.Label(label="● Ready", halign=Gtk.Align.START, css_classes=["status-pill-ready", "telemetry-pill"])
        self.status_label = Gtk.Label(label="Ready to stream", halign=Gtk.Align.START, hexpand=True, css_classes=["status-label"])
        self.status_label.set_ellipsize(Pango.EllipsizeMode.END)

        footer_row.append(self.status_pill)
        footer_row.append(self.status_label)

        self.est_time_pill = Gtk.Label(label="~0.0s", css_classes=["telemetry-pill", "telemetry-pill-time"])
        self.est_time_pill.set_tooltip_text("Estimated Transmission Duration")

        self.stats_pill = Gtk.Label(label="0 lines · 0 chars", css_classes=["telemetry-pill", "telemetry-pill-stats"])
        self.stats_label = self.stats_pill  # Backward compatibility alias

        self.cursor_pill = Gtk.Label(label="Ln 1, Col 1", css_classes=["telemetry-pill", "telemetry-pill-cursor"])
        self.cursor_pill.set_tooltip_text("Cursor Position (Line, Column)")

        self.encoding_pill = Gtk.Label(label="UTF-8", css_classes=["telemetry-pill", "telemetry-pill-dim"])

        footer_row.append(self.est_time_pill)
        footer_row.append(self.stats_pill)
        footer_row.append(self.cursor_pill)
        footer_row.append(self.encoding_pill)



        # Append structured sections to main container
        for s in (
            app_toolbar,
            editor_toolbar,
            self.tab_manager,
            self.find_bar,
            control_deck,
            action_row,
            self.progress_bar,
            footer_row,
        ):
            self.main_box.append(s)

    # ═══════════════════════════════════════════════════════
    #  TAB & EDITOR LISTENERS
    # ═══════════════════════════════════════════════════════

    def _setup_editor_listeners(self, editor: CodeEditor) -> None:
        """Attach listeners to a code editor."""
        editor.set_on_file_load(self._on_file_loaded)
        editor.get_buffer().connect("changed", lambda _: self._update_editor_stats())
        editor.get_buffer().connect("notify::cursor-position", lambda _b, _p: self._update_editor_stats())

    def _on_tab_changed(self, editor: CodeEditor, index: int) -> None:
        """Callback when the active tab is changed."""
        self._setup_editor_listeners(editor)

        # Sync language dropdown
        lang_id = editor.get_language_id()
        for i, (_, lid) in enumerate(SUPPORTED_LANGUAGES):
            if lid == lang_id:
                self.language_dropdown.set_selected(i)
                break

        # Sync find bar buffer
        self.find_bar._buffer = editor.get_buffer()
        self.find_bar._search_context = __import__("gi").repository.GtkSource.SearchContext.new(
            editor.get_buffer(), self.find_bar._search_settings
        )
        self.find_bar._search_context.set_highlight(True)

        self._update_editor_stats()

    # ═══════════════════════════════════════════════════════
    #  TOOLS POPOVER & ACTIONS
    # ═══════════════════════════════════════════════════════

    def _build_tools_popover(self) -> None:
        """Build popover for code tools, beautifiers, and visualizers with clean HD vector icons."""
        self.tools_popover = Gtk.Popover()
        self.tools_popover.add_css_class("popover-card")

        scroll = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
            max_content_height=420,
            propagate_natural_height=True,
        )
        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, css_classes=["popover-inner"])
        pop_box.set_size_request(280, -1)

        title = Gtk.Label(label="Code Tools & Transforms", halign=Gtk.Align.START, css_classes=["popover-title"])
        pop_box.append(title)

        # 1. AI & Simulation
        sec_sim = Gtk.Label(label="Simulation & AI", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_sim)

        btn_ai = _create_menu_row("system-run-symbolic", "Extract AI Markdown", "Ctrl+M", is_highlight=True)
        btn_ai.connect("clicked", lambda _: (self._apply_tool_action("extract_ai"), self.tools_popover.popdown()))
        pop_box.append(btn_ai)

        btn_sim = _create_menu_row("media-playback-start-symbolic", "Live Simulation Player", "Ctrl+Shift+P", is_highlight=True)
        btn_sim.connect("clicked", lambda _: (self._show_simulation_player(), self.tools_popover.popdown()))
        pop_box.append(btn_sim)

        btn_preview = _create_menu_row("edit-find-symbolic", "Pre-Flight Preview", "Ctrl+P")
        btn_preview.connect("clicked", lambda _: (self._show_dry_run_preview(), self.tools_popover.popdown()))
        pop_box.append(btn_preview)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 2. Formatters & Beautifiers
        sec_fmt = Gtk.Label(label="Code Formatters & Beautifiers", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_fmt)

        btn_fmt_auto = _create_menu_row("format-indent-more-symbolic", "Auto Format Code", "Ctrl+Shift+F")
        btn_fmt_auto.connect("clicked", lambda _: (self._apply_tool_action("format_auto"), self.tools_popover.popdown()))
        pop_box.append(btn_fmt_auto)

        btn_fmt_json = _create_menu_row("accessories-text-editor-symbolic", "Format JSON (Pretty 2-spaces)")
        btn_fmt_json.connect("clicked", lambda _: (self._apply_tool_action("format_json"), self.tools_popover.popdown()))
        pop_box.append(btn_fmt_json)

        btn_min_json = _create_menu_row("edit-clear-symbolic", "Minify JSON (Compact)")
        btn_min_json.connect("clicked", lambda _: (self._apply_tool_action("minify_json"), self.tools_popover.popdown()))
        pop_box.append(btn_min_json)

        btn_fmt_sql = _create_menu_row("view-list-bullet-symbolic", "Format SQL Query")
        btn_fmt_sql.connect("clicked", lambda _: (self._apply_tool_action("format_sql"), self.tools_popover.popdown()))
        pop_box.append(btn_fmt_sql)

        btn_fmt_html = _create_menu_row("format-text-bold-symbolic", "Format HTML / XML")
        btn_fmt_html.connect("clicked", lambda _: (self._apply_tool_action("format_html"), self.tools_popover.popdown()))
        pop_box.append(btn_fmt_html)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 3. Encoders & Data
        sec_enc = Gtk.Label(label="Data Encoders & Decoders", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_enc)

        btn_b64_enc = _create_menu_row("edit-copy-symbolic", "Base64 Encode")
        btn_b64_enc.connect("clicked", lambda _: (self._apply_tool_action("encode_b64"), self.tools_popover.popdown()))
        pop_box.append(btn_b64_enc)

        btn_b64_dec = _create_menu_row("edit-paste-symbolic", "Base64 Decode")
        btn_b64_dec.connect("clicked", lambda _: (self._apply_tool_action("decode_b64"), self.tools_popover.popdown()))
        pop_box.append(btn_b64_dec)

        btn_url_enc = _create_menu_row("insert-link-symbolic", "URL Percent Encode")
        btn_url_enc.connect("clicked", lambda _: (self._apply_tool_action("encode_url"), self.tools_popover.popdown()))
        pop_box.append(btn_url_enc)

        btn_url_dec = _create_menu_row("emblem-symbolic-link-symbolic", "URL Percent Decode")
        btn_url_dec.connect("clicked", lambda _: (self._apply_tool_action("decode_url"), self.tools_popover.popdown()))
        pop_box.append(btn_url_dec)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 4. Code Cleaning & Anti-Cheat Stealth
        sec_clean = Gtk.Label(label="Clean & Stealth", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_clean)

        btn_comments = _create_menu_row("edit-clear-symbolic", "Strip Comments & Docstrings")
        btn_comments.connect("clicked", lambda _: (self._apply_tool_action("strip_comments"), self.tools_popover.popdown()))
        pop_box.append(btn_comments)

        btn_auto_close = _create_menu_row("accessories-text-editor-symbolic", "Compensate Auto-Close Brackets")
        btn_auto_close.connect("clicked", lambda _: (self._apply_tool_action("compensate_brackets"), self.tools_popover.popdown()))
        pop_box.append(btn_auto_close)

        # Typo Rate Selector
        typo_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, margin_top=3, margin_bottom=3)
        typo_lbl = Gtk.Label(label="Typo Rate:", css_classes=["toolbar-label"])
        typo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["linked"])
        btn_t0 = Gtk.Button(label="Off", css_classes=["preset-btn"])
        btn_t1 = Gtk.Button(label="1%", css_classes=["preset-btn"])
        btn_t3 = Gtk.Button(label="3%", css_classes=["preset-btn"])

        def _set_typo(val: int):
            self._typo_rate = val
            self.set_status(f"Stealth typo simulation set to {val}%.")
            self.tools_popover.popdown()

        btn_t0.connect("clicked", lambda _: _set_typo(0))
        btn_t1.connect("clicked", lambda _: _set_typo(1))
        btn_t3.connect("clicked", lambda _: _set_typo(3))

        typo_box.append(btn_t0)
        typo_box.append(btn_t1)
        typo_box.append(btn_t3)
        typo_row.append(typo_lbl)
        typo_row.append(typo_box)
        pop_box.append(typo_row)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 5. Case Converters
        sec_case = Gtk.Label(label="Case Converters", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_case)

        btn_camel = _create_menu_row("format-text-symbolic", "Convert to camelCase")
        btn_camel.connect("clicked", lambda _: (self._apply_tool_action("case_camel"), self.tools_popover.popdown()))
        btn_snake = _create_menu_row("format-text-symbolic", "Convert to snake_case")
        btn_snake.connect("clicked", lambda _: (self._apply_tool_action("case_snake"), self.tools_popover.popdown()))
        btn_pascal = _create_menu_row("format-text-symbolic", "Convert to PascalCase")
        btn_pascal.connect("clicked", lambda _: (self._apply_tool_action("case_pascal"), self.tools_popover.popdown()))
        btn_const = _create_menu_row("format-text-symbolic", "Convert to CONSTANT_CASE")
        btn_const.connect("clicked", lambda _: (self._apply_tool_action("case_constant"), self.tools_popover.popdown()))
        pop_box.append(btn_camel)
        pop_box.append(btn_snake)
        pop_box.append(btn_pascal)
        pop_box.append(btn_const)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 6. String Literals & Escaping
        sec_esc = Gtk.Label(label="String & Literal Escaping", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_esc)

        btn_esc = _create_menu_row("edit-copy-symbolic", "Escape String (\\\", \\n, \\t)")
        btn_esc.connect("clicked", lambda _: (self._apply_tool_action("escape_str"), self.tools_popover.popdown()))
        btn_unesc = _create_menu_row("edit-paste-symbolic", "Unescape String Literals")
        btn_unesc.connect("clicked", lambda _: (self._apply_tool_action("unescape_str"), self.tools_popover.popdown()))
        pop_box.append(btn_esc)
        pop_box.append(btn_unesc)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 7. Indentation & Whitespace
        sec_indent = Gtk.Label(label="Indentation & Whitespace", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_indent)

        btn_tab4 = _create_menu_row("format-indent-more-symbolic", "Tabs → 4 Spaces")
        btn_tab4.connect("clicked", lambda _: (self._apply_tool_action("tabs_to_4"), self.tools_popover.popdown()))
        btn_sp2tab = _create_menu_row("format-indent-less-symbolic", "Spaces → Tabs")
        btn_sp2tab.connect("clicked", lambda _: (self._apply_tool_action("spaces_to_tabs"), self.tools_popover.popdown()))
        btn_trim = _create_menu_row("edit-clear-symbolic", "Trim Trailing Spaces")
        btn_trim.connect("clicked", lambda _: (self._apply_tool_action("trim_trailing"), self.tools_popover.popdown()))
        pop_box.append(btn_tab4)
        pop_box.append(btn_sp2tab)
        pop_box.append(btn_trim)

        pop_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL, css_classes=["popover-sep"]))

        # 8. Lines
        sec_lines = Gtk.Label(label="Line Operations", halign=Gtk.Align.START, css_classes=["popover-subtitle"])
        pop_box.append(sec_lines)

        btn_del_blank = _create_menu_row("user-trash-symbolic", "Remove Blank Lines")
        btn_del_blank.connect("clicked", lambda _: (self._apply_tool_action("remove_blank"), self.tools_popover.popdown()))
        btn_dedup = _create_menu_row("view-refresh-symbolic", "Deduplicate Lines")
        btn_dedup.connect("clicked", lambda _: (self._apply_tool_action("dedup"), self.tools_popover.popdown()))
        btn_sort = _create_menu_row("view-list-bullet-symbolic", "Sort Lines (A → Z)")
        btn_sort.connect("clicked", lambda _: (self._apply_tool_action("sort_az"), self.tools_popover.popdown()))
        btn_sort_rev = _create_menu_row("view-list-bullet-symbolic", "Sort Lines (Z → A)")
        btn_sort_rev.connect("clicked", lambda _: (self._apply_tool_action("sort_za"), self.tools_popover.popdown()))
        pop_box.append(btn_del_blank)
        pop_box.append(btn_dedup)
        pop_box.append(btn_sort)
        pop_box.append(btn_sort_rev)

        scroll.set_child(pop_box)
        self.tools_popover.set_child(scroll)
        self.tools_btn.set_popover(self.tools_popover)

    def _apply_tool_action(self, action: str) -> None:
        """Apply a code transformation to selection or entire editor."""
        editor = self._active_editor()
        sel = editor.get_selected_text()
        raw = sel if sel else editor.get_text()
        if not raw:
            return

        transformed = raw
        lang_id = editor.get_language_id()

        if action == "extract_ai":
            transformed = extract_markdown_code(raw)
        elif action == "strip_comments":
            transformed = strip_comments_and_docstrings(raw, lang_id)
        elif action == "compensate_brackets":
            transformed = compensate_auto_close(raw)
        elif action == "escape_str":
            transformed = escape_string(raw)
        elif action == "unescape_str":
            transformed = unescape_string(raw)
        elif action == "case_camel":
            transformed = change_case(raw, "camel")
        elif action == "case_snake":
            transformed = change_case(raw, "snake")
        elif action == "case_pascal":
            transformed = change_case(raw, "pascal")
        elif action == "case_constant":
            transformed = change_case(raw, "constant")
        elif action == "format_auto":
            if lang_id == "json":
                ok, res = format_json(raw, 2)
                transformed = res if ok else raw
                if not ok:
                    self.set_status(f"⚠ {res}")
                    return
            elif lang_id == "sql":
                transformed = format_sql(raw)
            elif lang_id in ("html", "xml"):
                transformed = format_html(raw, 2)
            else:
                transformed = convert_tabs_to_spaces(trim_trailing_whitespace(raw), 4)
        elif action == "format_json":
            ok, res = format_json(raw, 2)
            if ok:
                transformed = res
            else:
                self.set_status(f"⚠ {res}")
                return
        elif action == "minify_json":
            ok, res = minify_json(raw)
            if ok:
                transformed = res
            else:
                self.set_status(f"⚠ {res}")
                return
        elif action == "format_sql":
            transformed = format_sql(raw)
        elif action == "format_html":
            transformed = format_html(raw, 2)
        elif action == "encode_b64":
            transformed = encode_base64(raw)
        elif action == "decode_b64":
            ok, res = decode_base64(raw)
            if ok:
                transformed = res
            else:
                self.set_status(f"⚠ {res}")
                return
        elif action == "encode_url":
            transformed = encode_url(raw)
        elif action == "decode_url":
            transformed = decode_url(raw)
        elif action == "tabs_to_4":
            transformed = convert_tabs_to_spaces(raw, 4)
        elif action == "spaces_to_tabs":
            transformed = convert_spaces_to_tabs(raw, 4)
        elif action == "trim_trailing":
            transformed = trim_trailing_whitespace(raw)
        elif action == "remove_blank":
            transformed = remove_blank_lines(raw)
        elif action == "dedup":
            transformed = deduplicate_lines(raw)
        elif action == "sort_az":
            transformed = sort_lines(raw, reverse=False)
        elif action == "sort_za":
            transformed = sort_lines(raw, reverse=True)


        if sel:
            bounds = editor.get_buffer().get_selection_bounds()
            if bounds:
                start_iter, end_iter = bounds
                editor.get_buffer().delete(start_iter, end_iter)
                editor.get_buffer().insert_at_cursor(transformed)
        else:
            editor.set_text(transformed)

        self._update_editor_stats()
        self.set_status(f"Applied {action.replace('_', ' ').capitalize()}.")

    def _show_simulation_player(self) -> None:
        """Open the interactive real-time typing simulation visualizer modal."""
        selected_text = self._active_editor().get_selected_text()
        target_text = selected_text if selected_text else self._active_editor().get_text()
        if not target_text:
            self.set_status("Editor is empty — nothing to simulate.")
            return

        mode = self._get_current_mode()
        if mode == "strip":
            processed = strip_line_numbers(target_text)
        elif mode == "preserve":
            processed = preserve(target_text)
        else:
            processed = smart(target_text)

        if getattr(self, "_auto_close", False):
            processed = compensate_auto_close(processed)

        dlg = SimulationPlayerDialog(
            parent=self,
            text=processed,
            delay_ms=int(self.delay_spin.get_value()),
            language_id=self._active_editor().get_language_id(),
            enable_humanize=self.humanize_toggle.get_active(),
            typo_rate_pct=float(self._typo_rate) if self.humanize_toggle.get_active() else 0.0,
        )

        def _resp(d: Gtk.Dialog, resp: int):
            d.close()
            if resp == Gtk.ResponseType.OK:
                self._on_arm_and_type_clicked(self.arm_button)

        dlg.connect("response", _resp)
        dlg.present()

    def _show_preferences_dialog(self) -> None:
        """Open the comprehensive application preferences modal."""
        current_settings = self.settings_store.load()
        dlg = PreferencesDialog(
            parent=self,
            settings=current_settings,
            on_save=self._apply_preferences_update,
        )

        def _resp(d: Gtk.Dialog, resp: int):
            if resp == Gtk.ResponseType.OK:
                updated = d.get_updated_settings()
                self.settings_store.save(updated)
                self._apply_preferences_update(updated)
            d.close()

        dlg.connect("response", _resp)
        dlg.present()

    def _apply_preferences_update(self, settings: dict) -> None:
        """Apply newly saved settings immediately to the active window and editors."""
        if "default_delay_ms" in settings and hasattr(self, "delay_spin"):
            self.delay_spin.set_value(float(settings["default_delay_ms"]))
        if "default_countdown_sec" in settings and hasattr(self, "countdown_spin"):
            self.countdown_spin.set_value(float(settings["default_countdown_sec"]))
        if "default_mode" in settings and hasattr(self, "mode_smart_radio"):
            mode = settings["default_mode"]
            if mode == "preserve":
                self.mode_preserve_radio.set_active(True)
            elif mode == "strip":
                self.mode_strip_radio.set_active(True)
            else:
                self.mode_smart_radio.set_active(True)
        if "auto_close_compensate" in settings:
            self._auto_close = settings["auto_close_compensate"]
        if "humanize_cadence" in settings and hasattr(self, "humanize_toggle"):
            self.humanize_toggle.set_active(settings["humanize_cadence"])
        if "typo_rate" in settings:
            self._typo_rate = settings["typo_rate"]
        if "notify_on_complete" in settings:
            self._notify_on_complete = settings["notify_on_complete"]
        if "sound_chime" in settings:
            self._sound_chime = settings["sound_chime"]
        if "enable_tray" in settings:
            self._enable_tray = settings["enable_tray"]
        if "minimize_to_tray" in settings:
            self._minimize_to_tray = settings["minimize_to_tray"]

        # Apply editor styling to tab editors
        font_size = settings.get("font_size", 11)
        show_lines = settings.get("show_line_numbers", True)
        wrap = settings.get("word_wrap", False)
        highlight_line = settings.get("highlight_current_line", True)

        if hasattr(self, "tab_manager") and self.tab_manager:
            self.tab_manager.configure_editors(
                font_size=font_size,
                show_line_numbers=show_lines,
                word_wrap=wrap,
                highlight_current_line=highlight_line,
            )
        else:
            for ed in self._get_all_editors():
                ed.set_font_size(font_size)
                ed.set_show_line_numbers(show_lines)
                ed.set_word_wrap(wrap)
                ed.set_highlight_current_line(highlight_line)

        self.set_status("Preferences updated and applied.")


    def _get_all_editors(self) -> list:
        """Return list of all open CodeEditor instances across tabs."""
        if hasattr(self, "tab_manager") and self.tab_manager:
            return self.tab_manager.get_all_editors()
        if hasattr(self, "editor") and self.editor:
            return [self.editor]
        return []

    def _show_dry_run_preview(self) -> None:
        """Open the pre-flight dry-run typing preview modal."""
        selected_text = self._active_editor().get_selected_text()
        target_text = selected_text if selected_text else self._active_editor().get_text()
        if not target_text:
            self.set_status("Editor is empty — nothing to preview.")
            return

        mode = self._get_current_mode()

        if mode == "strip":
            processed = strip_line_numbers(target_text)
        elif mode == "preserve":
            processed = preserve(target_text)
        else:
            processed = smart(target_text)

        dlg = DryRunPreviewDialog(
            parent=self,
            processed_text=processed,
            delay_ms=int(self.delay_spin.get_value()),
            mode=mode,
            language_id=self._active_editor().get_language_id(),
            enable_humanize=self.humanize_toggle.get_active(),
        )

        def _resp(d, resp):
            if resp == Gtk.ResponseType.OK:
                d.close()
                self._on_arm_and_type_clicked(self.arm_button)
            else:
                d.close()

        dlg.connect("response", _resp)
        dlg.present()

    # ═══════════════════════════════════════════════════════
    #  TEMPLATES POPOVER
    # ═══════════════════════════════════════════════════════

    def _build_templates_popover(self) -> None:
        """Build popover for starter templates with clean language badges."""
        self.templates_popover = Gtk.Popover()
        self.templates_popover.add_css_class("popover-card")

        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, css_classes=["popover-inner"])

        title = Gtk.Label(label="Starter Code Boilerplates", halign=Gtk.Align.START, css_classes=["popover-title"])
        pop_box.append(title)

        listbox = Gtk.ListBox(css_classes=["popover-listbox"])
        scroll = Gtk.ScrolledWindow(child=listbox, min_content_height=200, min_content_width=270, max_content_height=320)

        for tmpl in STARTER_TEMPLATES:
            row = Gtk.ListBoxRow(css_classes=["template-row"])
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
            icon.set_icon_size(Gtk.IconSize.NORMAL)
            row_box.append(icon)

            row_box.append(Gtk.Label(label=tmpl.title, halign=Gtk.Align.START, hexpand=True, css_classes=["template-title"]))

            lang_badge = Gtk.Label(label=tmpl.language_id.upper(), halign=Gtk.Align.END, css_classes=["template-badge"])
            row_box.append(lang_badge)

            row.set_child(row_box)
            listbox.append(row)

        listbox.connect("row-activated", self._on_template_row_activated)
        pop_box.append(scroll)

        self.templates_popover.set_child(pop_box)
        self.templates_btn.set_popover(self.templates_popover)

    def _on_template_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        idx = row.get_index()
        if 0 <= idx < len(STARTER_TEMPLATES):
            tmpl = STARTER_TEMPLATES[idx]
            cur_text = self._active_editor().get_text()
            if cur_text and cur_text.strip():
                dlg = ConfirmReplaceDialog(parent=self)
                dlg.connect(
                    "response",
                    lambda d, r: (d.close(), self._insert_template(tmpl), self.templates_popover.popdown())
                    if r == Gtk.ResponseType.OK
                    else d.close(),
                )
                dlg.present()
            else:
                self._insert_template(tmpl)
                self.templates_popover.popdown()

    def _insert_template(self, tmpl: CodeTemplate) -> None:
        self._active_editor().set_text(tmpl.content)
        self._set_language_by_id(tmpl.language_id)
        self.set_status(f"Loaded template: {tmpl.title}")

    # ═══════════════════════════════════════════════════════
    #  POPOVERS (HISTORY & SESSION LOGS)
    # ═══════════════════════════════════════════════════════

    def _build_history_popover(self) -> None:
        """Build popover panel for recent snippets."""
        self.history_popover = Gtk.Popover()
        self.history_popover.add_css_class("popover-card")

        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, css_classes=["popover-inner"])

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.history_popover_title = Gtk.Label(label="Recent Snippets (0)", halign=Gtk.Align.START, hexpand=True, css_classes=["popover-title"])
        self.clear_history_btn = self._create_icon_button("edit-clear-symbolic", "Clear All", "Clear snippet history", css_classes=["clear-history-btn"])
        self.clear_history_btn.connect("clicked", self._on_clear_history_clicked)
        header_box.append(self.history_popover_title)
        header_box.append(self.clear_history_btn)
        pop_box.append(header_box)

        self.recent_listbox = Gtk.ListBox(css_classes=["popover-listbox"])
        self.recent_listbox.connect("row-activated", self._on_recent_row_activated)
        scroll = Gtk.ScrolledWindow(
            child=self.recent_listbox,
            css_classes=["recent-scroll"],
            min_content_height=140,
            min_content_width=280,
            max_content_height=260,
        )
        pop_box.append(scroll)

        self.history_popover.set_child(pop_box)
        self.history_btn.set_popover(self.history_popover)

    def _build_sessions_popover(self) -> None:
        """Build popover panel for session logs with analytics summary and CSV export."""
        self.sessions_popover = Gtk.Popover()
        self.sessions_popover.add_css_class("popover-card")

        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6, css_classes=["popover-inner"])

        # Title & Action Row
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.sessions_popover_title = Gtk.Label(label="Session Log (0)", halign=Gtk.Align.START, hexpand=True, css_classes=["popover-title"])

        self.export_sessions_btn = self._create_icon_button("document-save-symbolic", "CSV", "Export session logs as CSV", css_classes=["clear-history-btn"])
        self.export_sessions_btn.connect("clicked", self._on_export_sessions_csv_clicked)

        self.clear_sessions_btn = self._create_icon_button("edit-clear-symbolic", "Clear", "Clear all session logs", css_classes=["clear-history-btn"])
        self.clear_sessions_btn.connect("clicked", self._on_clear_sessions_clicked)

        header_box.append(self.sessions_popover_title)
        header_box.append(self.export_sessions_btn)
        header_box.append(self.clear_sessions_btn)
        pop_box.append(header_box)

        # Analytics Summary Card
        self.analytics_summary_label = Gtk.Label(
            label="Total Typed: 0 chars · Avg Speed: 0 WPM",
            halign=Gtk.Align.START,
            css_classes=["popover-subtitle"],
        )
        pop_box.append(self.analytics_summary_label)

        self.session_listbox = Gtk.ListBox(css_classes=["popover-listbox"])
        scroll = Gtk.ScrolledWindow(
            child=self.session_listbox,
            css_classes=["session-log-scroll"],
            min_content_height=140,
            min_content_width=320,
            max_content_height=260,
        )
        pop_box.append(scroll)

        self.sessions_popover.set_child(pop_box)
        self.sessions_btn.set_popover(self.sessions_popover)

    def _on_export_sessions_csv_clicked(self, _button: Gtk.Button) -> None:
        """Export session logs as a CSV file."""
        if not self._session_logs:
            return
        dialog = Gtk.FileDialog()
        dialog.set_title("Export Sessions to CSV")
        dialog.set_initial_name("codewriter_sessions.csv")
        dialog.save(self, None, self._on_export_csv_response)

    def _on_export_csv_response(self, dialog, result) -> None:
        try:
            gfile = dialog.save_finish(result)
            if gfile:
                filepath = gfile.get_path()
                if filepath:
                    import csv
                    with open(filepath, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["Timestamp", "Characters", "Duration_ms", "WPM", "Mode", "Language", "Status"])
                        for s in self._session_logs:
                            writer.writerow([
                                s.get("timestamp", ""),
                                s.get("char_count", 0),
                                s.get("duration_ms", 0),
                                s.get("wpm", 0),
                                s.get("mode", ""),
                                s.get("language", ""),
                                s.get("status", ""),
                            ])
                    self.set_status(f"Exported {len(self._session_logs)} sessions to CSV.")
        except GLib.Error:
            pass

    # ═══════════════════════════════════════════════════════
    #  ACTIVE EDITOR HELPER
    # ═══════════════════════════════════════════════════════

    def _active_editor(self) -> CodeEditor:
        """Return the currently active CodeEditor from the tab manager."""
        return self.tab_manager.get_active_editor()

    # ═══════════════════════════════════════════════════════
    #  FILE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _on_open_file_clicked(self, _button: Optional[Gtk.Button] = None) -> None:
        """Open a file dialog and load the selected file into the editor."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open File")
        dialog.open(self, None, self._on_open_file_response)

    def _on_open_file_response(self, dialog, result) -> None:
        try:
            gfile = dialog.open_finish(result)
            if gfile:
                filepath = gfile.get_path()
                if filepath:
                    editor = self._active_editor()
                    if editor.load_file(filepath):
                        self.tab_manager._update_tab_titles()
                        basename = os.path.basename(filepath)
                        self.set_status(f"Loaded: {basename}")
                    else:
                        self.set_status("Failed to load file.")
        except GLib.Error:
            pass  # User cancelled

    def _on_save_file_clicked(self, _button: Optional[Gtk.Button] = None) -> None:
        """Save the current editor content to a file."""
        editor = self._active_editor()
        if editor.get_loaded_filepath():
            if editor.save_file():
                self.tab_manager._update_tab_titles()
                basename = os.path.basename(editor.get_loaded_filepath())
                self.set_status(f"Saved: {basename}")
            else:
                self.set_status("Save failed.")
        else:
            dialog = Gtk.FileDialog()
            dialog.set_title("Save File")
            dialog.save(self, None, self._on_save_file_response)

    def _on_save_file_response(self, dialog, result) -> None:
        try:
            gfile = dialog.save_finish(result)
            if gfile:
                filepath = gfile.get_path()
                if filepath:
                    editor = self._active_editor()
                    if editor.save_file(filepath):
                        self.tab_manager._update_tab_titles()
                        basename = os.path.basename(filepath)
                        self.set_status(f"Saved: {basename}")
                    else:
                        self.set_status("Save failed.")
        except GLib.Error:
            pass  # User cancelled

    def _on_file_loaded(self, filepath: str, lang_id: str) -> None:
        """Callback when a file is loaded via drag-and-drop or Open."""
        self._set_language_by_id(lang_id)
        self.tab_manager._update_tab_titles()
        basename = os.path.basename(filepath)
        self.set_status(f"Loaded: {basename}")

    # ═══════════════════════════════════════════════════════
    #  FIND & REPLACE
    # ═══════════════════════════════════════════════════════

    def _show_find(self) -> None:
        """Show the find bar."""
        self.find_bar._buffer = self._active_editor().get_buffer()
        self.find_bar._search_context = __import__("gi").repository.GtkSource.SearchContext.new(
            self._active_editor().get_buffer(), self.find_bar._search_settings
        )
        self.find_bar._search_context.set_highlight(True)
        self.find_bar.show_find()

    def _show_find_replace(self) -> None:
        """Show the find & replace bar."""
        self.find_bar._buffer = self._active_editor().get_buffer()
        self.find_bar._search_context = __import__("gi").repository.GtkSource.SearchContext.new(
            self._active_editor().get_buffer(), self.find_bar._search_settings
        )
        self.find_bar._search_context.set_highlight(True)
        self.find_bar.show_find_replace()

    # ═══════════════════════════════════════════════════════
    #  SHORTCUTS
    # ═══════════════════════════════════════════════════════

    def _on_show_shortcuts(self, _button=None) -> None:
        """Show the keyboard shortcuts window."""
        win = create_shortcuts_window(self)
        win.present()

    # ═══════════════════════════════════════════════════════
    #  EDITOR STATS & SELECTION AWARENESS
    # ═══════════════════════════════════════════════════════


    def _update_editor_stats(self) -> None:
        stats = self._active_editor().get_stats()
        lines = stats.get("lines", 0)
        chars = stats.get("chars", 0)
        words = stats.get("words", 0)
        sel_chars = stats.get("selected_chars", 0)
        cursor_line = stats.get("cursor_line", 1)
        cursor_col = stats.get("cursor_col", 1)

        # Estimate duration with cognitive pause overhead
        delay_ms = float(self.delay_spin.get_value()) if hasattr(self, "delay_spin") else 8.0
        active_chars = sel_chars if sel_chars > 0 else chars
        est_sec = (active_chars * delay_ms) / 1000.0 if active_chars > 0 else 0.0
        if hasattr(self, "humanize_toggle") and self.humanize_toggle.get_active():
            est_sec *= 1.35

        if est_sec < 60:
            est_str = f"~{est_sec:.1f}s"
        else:
            est_str = f"~{int(est_sec // 60)}m {int(est_sec % 60)}s"

        if hasattr(self, "est_time_pill"):
            self.est_time_pill.set_text(est_str)

        if hasattr(self, "cursor_pill"):
            self.cursor_pill.set_text(f"Ln {cursor_line}, Col {cursor_col}")

        if sel_chars > 0:
            self.stats_pill.set_text(f"{lines} lines · {chars} chars · {words} words ({sel_chars} sel)")
            if hasattr(self, "arm_button_label") and self.state == AppState.IDLE:
                self.arm_button_label.set_text(f"ARM & TYPE Selection ({sel_chars} chars)")
        else:
            self.stats_pill.set_text(f"{lines} lines · {chars} chars · {words} words")
            if hasattr(self, "arm_button_label") and self.state == AppState.IDLE:
                self.arm_button_label.set_text("ARM & TYPE (Ctrl+Enter)")


    # ═══════════════════════════════════════════════════════
    #  PROFILES
    # ═══════════════════════════════════════════════════════

    def _populate_profiles_dropdown(self, selected_name: str = "Default") -> None:
        names = [p.get("name", "Default") for p in self._profiles]
        self.profile_dropdown.set_model(Gtk.StringList.new(names))
        idx = next((i for i, n in enumerate(names) if n == selected_name), 0)
        self.profile_dropdown.set_selected(idx)
        self._update_delete_button_sensitivity(names[idx] if names else "Default")

    def _update_delete_button_sensitivity(self, profile_name: str) -> None:
        self.delete_profile_btn.set_sensitive(profile_name != "Default")

    # ═══════════════════════════════════════════════════════
    #  RECENT SNIPPETS
    # ═══════════════════════════════════════════════════════

    def _refresh_recent_snippets(self) -> None:
        self._recent_snippets = self.snippet_store.load()
        count = len(self._recent_snippets)

        # Update History Button child
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        icon = Gtk.Image.new_from_icon_name("document-open-recent-symbolic")
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        box.append(icon)
        box.append(Gtk.Label(label=f"History ({count})"))
        self.history_btn.set_child(box)

        if hasattr(self, "history_popover_title"):
            self.history_popover_title.set_text(f"Recent Snippets ({count})")
        self.clear_history_btn.set_sensitive(count > 0)

        while child := self.recent_listbox.get_first_child():
            self.recent_listbox.remove(child)

        for snip in self._recent_snippets:
            row = Gtk.ListBoxRow(css_classes=["recent-row"])
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
            icon.set_icon_size(Gtk.IconSize.NORMAL)
            row_box.append(icon)

            row_box.append(
                Gtk.Label(
                    label=snip.get("title", "Snippet"),
                    halign=Gtk.Align.START,
                    hexpand=True,
                    css_classes=["recent-title"],
                )
            )

            del_btn = self._create_icon_button("user-trash-symbolic", None, "Delete snippet", css_classes=["recent-delete-btn"])
            snip_id = snip.get("id")
            del_btn.connect("clicked", lambda _, sid=snip_id: self._on_delete_snippet_clicked(sid))
            row_box.append(del_btn)

            row.set_child(row_box)
            self.recent_listbox.append(row)

    def _on_delete_snippet_clicked(self, snippet_id: str) -> None:
        self.snippet_store.delete(snippet_id)
        self._refresh_recent_snippets()

    def _on_clear_history_clicked(self, _button: Gtk.Button) -> None:
        self.snippet_store.clear()
        self._refresh_recent_snippets()

    def _on_recent_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if (idx := row.get_index()) < 0 or idx >= len(self._recent_snippets):
            return
        snip = self._recent_snippets[idx]
        cur_text = self._active_editor().get_text()
        if cur_text and cur_text != snip["content"]:
            dlg = ConfirmReplaceDialog(parent=self)
            dlg.connect(
                "response",
                lambda d, r: (d.close(), self._load_snippet_content(snip), self.history_popover.popdown())
                if r == Gtk.ResponseType.OK
                else d.close(),
            )
            dlg.present()
        else:
            self._load_snippet_content(snip)
            self.history_popover.popdown()

    def _load_snippet_content(self, snip: dict) -> None:
        self._active_editor().set_text(snip["content"])
        if lang := snip.get("language"):
            self._set_language_by_id(lang)

    # ═══════════════════════════════════════════════════════
    #  SESSION LOG & ANALYTICS
    # ═══════════════════════════════════════════════════════

    def _refresh_session_logs(self) -> None:
        self._session_logs = self.session_log_store.load()
        count = len(self._session_logs)

        # Update Sessions Button child
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        icon = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic")
        icon.set_icon_size(Gtk.IconSize.NORMAL)
        box.append(icon)
        box.append(Gtk.Label(label=f"Logs ({count})"))
        self.sessions_btn.set_child(box)

        if hasattr(self, "sessions_popover_title"):
            self.sessions_popover_title.set_text(f"Session Log ({count})")
        self.clear_sessions_btn.set_sensitive(count > 0)
        self.export_sessions_btn.set_sensitive(count > 0)

        # Update Analytics Summary
        if hasattr(self, "analytics_summary_label"):
            total_chars = sum(s.get("char_count", 0) for s in self._session_logs)
            wpms = [s.get("wpm", 0) for s in self._session_logs if s.get("wpm", 0) > 0]
            avg_wpm = int(sum(wpms) / len(wpms)) if wpms else 0
            self.analytics_summary_label.set_text(f"All-Time: {total_chars:,} chars · {count} sessions · Avg {avg_wpm} WPM")

        while child := self.session_listbox.get_first_child():
            self.session_listbox.remove(child)

        for session in self._session_logs[:20]:  # Show last 20 in UI
            row = Gtk.ListBoxRow(css_classes=["session-log-row"])
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            # Timestamp
            ts = session.get("timestamp", "")
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(ts)
                ts_display = dt.strftime("%b %d %H:%M")
            except Exception:
                ts_display = ts[:16]

            row_box.append(Gtk.Label(label=ts_display, css_classes=["session-stat-label"]))

            # Char count
            chars = session.get("char_count", 0)
            row_box.append(Gtk.Label(label=f"{chars} chars", css_classes=["session-stat-label", "session-stat-accent"]))

            # Duration
            dur_ms = session.get("duration_ms", 0)
            if dur_ms >= 60000:
                dur_display = f"{dur_ms / 60000:.1f}m"
            elif dur_ms >= 1000:
                dur_display = f"{dur_ms / 1000:.1f}s"
            else:
                dur_display = f"{dur_ms}ms"
            row_box.append(Gtk.Label(label=dur_display, css_classes=["session-stat-label"]))

            # WPM
            wpm = session.get("wpm", 0)
            wpm_class = "session-stat-success" if wpm > 100 else "session-stat-warning" if wpm > 50 else "session-stat-label"
            row_box.append(Gtk.Label(label=f"{wpm} WPM", css_classes=["session-stat-label", wpm_class]))

            # Status
            status = session.get("status", "complete")
            status_class = "session-stat-success" if status == "complete" else "session-stat-danger"
            row_box.append(Gtk.Label(label=status, css_classes=["session-stat-label", status_class], hexpand=True, halign=Gtk.Align.END))

            row.set_child(row_box)
            self.session_listbox.append(row)

    def _on_clear_sessions_clicked(self, _button: Gtk.Button) -> None:
        self.session_log_store.clear()
        self._refresh_session_logs()

    # ═══════════════════════════════════════════════════════
    #  PROFILE OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _on_profile_selected(self, dropdown: Gtk.DropDown, _pspec) -> None:
        if (idx := dropdown.get_selected()) == Gtk.INVALID_LIST_POSITION or idx >= len(self._profiles):
            return
        p = self._profiles[idx]
        prof_name = p.get("name", "Default")
        self._update_delete_button_sensitivity(prof_name)

        self.delay_spin.set_value(float(p.get("delay_ms", 5)))
        self.countdown_spin.set_value(float(p.get("countdown_sec", 3)))

        mode = p.get("mode", "smart")
        if mode == "strip":
            self.mode_strip_radio.set_active(True)
        elif mode == "preserve":
            self.mode_preserve_radio.set_active(True)
        else:
            self.mode_smart_radio.set_active(True)

        if lang := p.get("language"):
            self._set_language_by_id(lang)

    def _on_language_selected(self, dropdown: Gtk.DropDown, _pspec) -> None:
        idx = dropdown.get_selected()
        if 0 <= idx < len(SUPPORTED_LANGUAGES):
            lang_id = SUPPORTED_LANGUAGES[idx][1]
            self._active_editor().set_language(lang_id)

    def _set_language_by_id(self, lang_id: str) -> None:
        for i, (_, lid) in enumerate(SUPPORTED_LANGUAGES):
            if lid == lang_id:
                self.language_dropdown.set_selected(i)
                self._active_editor().set_language(lang_id)
                break

    def _on_save_profile_clicked(self, _button: Gtk.Button) -> None:
        idx = self.profile_dropdown.get_selected()
        cur_name = self._profiles[idx]["name"] if idx < len(self._profiles) else "Default"
        dlg = ProfileNameDialog(parent=self, default_name=cur_name)

        def _resp(d, resp):
            if resp == Gtk.ResponseType.OK and (name := d.get_profile_name()):
                mode = "smart"
                if self.mode_preserve_radio.get_active():
                    mode = "preserve"
                elif self.mode_strip_radio.get_active():
                    mode = "strip"

                self._profiles = self.profile_store.upsert({
                    "name": name,
                    "target": "",
                    "language": self._active_editor().get_language_id(),
                    "mode": mode,
                    "delay_ms": int(self.delay_spin.get_value()),
                    "countdown_sec": int(self.countdown_spin.get_value()),
                })
                self._populate_profiles_dropdown(selected_name=name)
            d.close()

        dlg.connect("response", _resp)
        dlg.present()

    def _on_delete_profile_clicked(self, _button: Gtk.Button) -> None:
        idx = self.profile_dropdown.get_selected()
        if idx >= len(self._profiles):
            return
        prof_name = self._profiles[idx]["name"]
        if prof_name == "Default":
            return

        dlg = ConfirmDeleteProfileDialog(profile_name=prof_name, parent=self)

        def _resp(d, resp):
            if resp == Gtk.ResponseType.OK:
                self._profiles = self.profile_store.delete(prof_name)
                self._populate_profiles_dropdown(selected_name="Default")
            d.close()

        dlg.connect("response", _resp)
        dlg.present()

    # ═══════════════════════════════════════════════════════
    #  CLEAR EDITOR
    # ═══════════════════════════════════════════════════════

    def _on_clear_clicked(self, _button: Optional[Gtk.Button] = None) -> None:
        if not self._active_editor().get_text():
            return
        dlg = ConfirmClearDialog(parent=self)

        def _resp(d, resp):
            if resp == Gtk.ResponseType.OK:
                self._active_editor().clear()
                self.tab_manager._update_tab_titles()
            d.close()

        dlg.connect("response", _resp)
        dlg.present()

    # ═══════════════════════════════════════════════════════
    #  WINDOW CLOSE
    # ═══════════════════════════════════════════════════════

    def _on_close_request(self, _win) -> bool:
        idx = self.profile_dropdown.get_selected()
        prof_name = self._profiles[idx]["name"] if idx < len(self._profiles) else "Default"
        self.settings_store.save({
            "window_width": self.get_width() or 780,
            "window_height": self.get_height() or 640,
            "last_selected_profile": prof_name,
            "notify_on_complete": self._notify_on_complete,
            "humanize_cadence": self.humanize_toggle.get_active(),
            "typo_rate": self._typo_rate,
            "auto_close_compensate": getattr(self, "_auto_close", False),
            "enable_tray": getattr(self, "_enable_tray", True),
            "minimize_to_tray": getattr(self, "_minimize_to_tray", False),
        })
        if getattr(self, "_minimize_to_tray", False):
            app = self.get_application()
            if app and hasattr(app, "tray") and app.tray:
                self.hide()
                app.tray.set_window_visible(False)
                return True
        return False

    def toggle_visibility(self) -> None:
        """Toggle window between presented and hidden states."""
        if self.is_visible():
            self.hide()
            app = self.get_application()
            if app and hasattr(app, "tray") and app.tray:
                app.tray.set_window_visible(False)
        else:
            self.present()
            app = self.get_application()
            if app and hasattr(app, "tray") and app.tray:
                app.tray.set_window_visible(True)

    def arm_simulation(self) -> None:
        """Trigger ARM & TYPE simulation from tray or shortcut."""
        if self.state == AppState.IDLE:
            self._on_arm_and_type_clicked(self.arm_button)

    def pause_or_resume_simulation(self) -> None:
        """Toggle pause/resume simulation state."""
        if self.state == AppState.TYPING:
            self._on_pause_clicked(self.pause_button)
        elif self.state == AppState.PAUSED:
            self._on_resume_clicked(self.resume_button)

    def stop_simulation(self) -> None:
        """Stop/cancel active simulation."""
        if self.state in (AppState.COUNTDOWN, AppState.TYPING, AppState.PAUSED):
            self._on_stop_clicked(self.stop_button)

    def open_preferences(self) -> None:
        """Open application preferences modal."""
        self._show_preferences_dialog()

    def open_simulation_player(self) -> None:
        """Open live simulation player modal."""
        self._show_simulation_player()


    # ═══════════════════════════════════════════════════════
    #  KEYBOARD SHORTCUTS
    # ═══════════════════════════════════════════════════════

    def _on_key_pressed(self, _ctrl, keyval: int, _keycode: int, state: Gdk.ModifierType) -> bool:
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)
        alt = bool(state & Gdk.ModifierType.ALT_MASK)

        if keyval == Gdk.KEY_Escape:
            if self.find_bar.is_visible_bar():
                self.find_bar.hide_bar()
                return True
            self._on_stop_clicked(self.stop_button)
            return True

        # Space bar toggles Pause / Resume during active typing or paused state
        if keyval == Gdk.KEY_space and not ctrl and self.state in (AppState.TYPING, AppState.PAUSED):
            if self.state == AppState.TYPING:
                self._on_pause_clicked()
            else:
                self._on_resume_clicked()
            return True

        # Alt shortcuts
        if alt and not ctrl:
            if keyval == Gdk.KEY_Up:
                self._active_editor().move_current_line(-1)
                return True
            if keyval == Gdk.KEY_Down:
                self._active_editor().move_current_line(1)
                return True
            if keyval in (Gdk.KEY_z, Gdk.KEY_Z):
                is_wrapped = self._active_editor().toggle_word_wrap()
                self.set_status(f"Word wrap {'enabled' if is_wrapped else 'disabled'}.")
                return True

        if ctrl:
            # Ctrl+Enter — ARM & TYPE
            if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_ISO_Enter):
                if self.state == AppState.IDLE:
                    self._on_arm_and_type_clicked(self.arm_button)
                    return True

            # Ctrl+Shift+P — Live Simulation Player
            if keyval in (Gdk.KEY_P, Gdk.KEY_p) and shift:
                self._show_simulation_player()
                return True

            # Ctrl+P — Pre-flight dry-run preview
            if keyval == Gdk.KEY_p and not shift:
                self._show_dry_run_preview()
                return True

            # Ctrl+Shift+F — Auto Format Code
            if keyval in (Gdk.KEY_F, Gdk.KEY_f) and shift:
                self._apply_tool_action("format_auto")
                return True

            # Ctrl+Shift+D — Duplicate Line / Selection
            if keyval in (Gdk.KEY_D, Gdk.KEY_d) and shift:
                self._active_editor().duplicate_current_line_or_selection()
                self._update_editor_stats()
                return True

            # Ctrl+Shift+K — Delete Line
            if keyval in (Gdk.KEY_K, Gdk.KEY_k) and shift:
                self._active_editor().delete_current_line()
                self._update_editor_stats()
                return True

            # Ctrl+, — Preferences Dialog
            if keyval == Gdk.KEY_comma:
                self._show_preferences_dialog()
                return True

            # Ctrl++ / Ctrl+= — Zoom In
            if keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
                new_sz = self._active_editor().zoom_in()
                self.set_status(f"Editor font size: {new_sz}pt")
                return True

            # Ctrl+- — Zoom Out
            if keyval in (Gdk.KEY_minus, Gdk.KEY_KP_Subtract):
                new_sz = self._active_editor().zoom_out()
                self.set_status(f"Editor font size: {new_sz}pt")
                return True

            # Ctrl+0 — Reset Zoom
            if keyval in (Gdk.KEY_0, Gdk.KEY_KP_0):
                new_sz = self._active_editor().reset_zoom()
                self.set_status(f"Editor font size reset to {new_sz}pt")
                return True

            # Ctrl+M — Extract AI Markdown code block
            if keyval == Gdk.KEY_m:
                self._apply_tool_action("extract_ai")
                return True

            # Ctrl+O — Open file
            if keyval == Gdk.KEY_o:
                self._on_open_file_clicked(None)
                return True

            # Ctrl+S — Save file
            if keyval == Gdk.KEY_s:
                self._on_save_file_clicked(None)
                return True

            # Ctrl+F — Find
            if keyval == Gdk.KEY_f:
                self._show_find()
                return True

            # Ctrl+H — Find & Replace
            if keyval == Gdk.KEY_h:
                self._show_find_replace()
                return True

            # Ctrl+L — Clear editor
            if keyval == Gdk.KEY_l:
                self._on_clear_clicked(None)
                return True

            # Ctrl+? — Show shortcuts
            if keyval in (Gdk.KEY_question, Gdk.KEY_slash):
                self._on_show_shortcuts()
                return True

            # Ctrl+1/2/3 — Speed presets
            if keyval == Gdk.KEY_1:
                self.delay_spin.set_value(float(PRESET_FAST_MS))
                return True
            if keyval == Gdk.KEY_2:
                self.delay_spin.set_value(float(PRESET_NORMAL_MS))
                return True
            if keyval == Gdk.KEY_3:
                self.delay_spin.set_value(float(PRESET_SAFE_MS))
                return True

        return False


    # ═══════════════════════════════════════════════════════
    #  STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════

    def _set_state(self, new_state: AppState) -> None:
        self.state = new_state
        is_idle = new_state == AppState.IDLE
        is_active = new_state in (AppState.COUNTDOWN, AppState.TYPING, AppState.PAUSED)
        is_typing = new_state == AppState.TYPING
        is_paused = new_state == AppState.PAUSED

        for w in (
            self.delay_spin,
            self.countdown_spin,
            self.mode_smart_radio,
            self.mode_preserve_radio,
            self.mode_strip_radio,
            self.preset_fast_btn,
            self.preset_normal_btn,
            self.preset_safe_btn,
            self.humanize_toggle,
            self.profile_dropdown,
            self.save_profile_btn,
            self.history_btn,
            self.sessions_btn,
            self.shortcuts_btn,
            self.tools_btn,
            self.templates_btn,
            self.language_dropdown,
            self.paste_btn,
            self.copy_btn,
            self.clear_btn,
            self.clear_history_btn,
            self.export_sessions_btn,
            self.open_btn,
            self.save_btn,
        ):

            w.set_sensitive(is_idle)

        if is_idle:
            idx = self.profile_dropdown.get_selected()
            prof_name = self._profiles[idx]["name"] if idx < len(self._profiles) else "Default"
            self._update_delete_button_sensitivity(prof_name)
        else:
            self.delete_profile_btn.set_sensitive(False)

        self._active_editor().get_view().set_editable(is_idle)
        self.arm_button.set_sensitive(is_idle)
        self.arm_button.set_visible(is_idle)

        self.pause_button.set_sensitive(is_typing)
        self.pause_button.set_visible(is_typing)

        self.resume_button.set_sensitive(is_paused)
        self.resume_button.set_visible(is_paused)

        self.stop_button.set_sensitive(is_active)
        self.stop_button.set_visible(is_active)
        self.progress_bar.set_visible(is_active)

        app = self.get_application()
        if app and hasattr(app, "tray") and app.tray:
            state_map = {
                AppState.IDLE: "idle",
                AppState.COUNTDOWN: "countdown",
                AppState.TYPING: "typing",
                AppState.PAUSED: "paused",
            }
            app.tray.set_state(state_map.get(new_state, "idle"))

    # ═══════════════════════════════════════════════════════
    #  TYPING OPERATIONS
    # ═══════════════════════════════════════════════════════

    def _get_current_mode(self) -> str:
        """Return the current text processing mode as a string."""
        if self.mode_preserve_radio.get_active():
            return "preserve"
        elif self.mode_strip_radio.get_active():
            return "strip"
        return "smart"

    def _on_arm_and_type_clicked(self, _button: Gtk.Button) -> None:
        selected_text = self._active_editor().get_selected_text()
        if selected_text:
            self._active_target_text = selected_text
            self._is_typing_selection = True
        else:
            self._active_target_text = self._active_editor().get_text()
            self._is_typing_selection = False

        if not self._active_target_text:
            self.set_status("Editor is empty — nothing to type.")
            return

        self._set_state(AppState.COUNTDOWN)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("0 / 0 characters")
        self.progress_bar.set_show_text(True)

        desc = "selection" if self._is_typing_selection else "text"

        def _on_tick(rem: int):
            self.set_status(f"Starting in {rem}... ({desc})")
            if getattr(self, "_sound_chime", True):
                play_tick()

        self.countdown_overlay.start(
            seconds=int(self.countdown_spin.get_value()),
            on_tick=_on_tick,
            on_complete=self._do_type,
            on_cancel=lambda: (self.set_status("Cancelled."), self._set_state(AppState.IDLE)),
        )

    def _on_pause_clicked(self, _button: Optional[Gtk.Button] = None) -> None:
        if self.state == AppState.TYPING:
            self.typing_controller.pause()
            self._set_state(AppState.PAUSED)
            self.set_status("⏸ Paused — press Resume or Space to continue.")

    def _on_resume_clicked(self, _button: Optional[Gtk.Button] = None) -> None:
        if self.state == AppState.PAUSED:
            self.typing_controller.resume()
            self._set_state(AppState.TYPING)
            self.set_status("▶ Resumed typing...")

    def _on_stop_clicked(self, _button: Gtk.Button) -> None:
        if self.state == AppState.COUNTDOWN:
            self.countdown_overlay.cancel()
        elif self.state in (AppState.TYPING, AppState.PAUSED):
            self.typing_controller.cancel()

    def _do_type(self) -> None:
        self._set_state(AppState.TYPING)
        self._typing_start_time = time.monotonic()
        raw_text = self._active_target_text

        # Save to snippet store with current language
        self.snippet_store.add(raw_text, language=self._active_editor().get_language_id())
        self._refresh_recent_snippets()

        # Apply text processing mode
        mode = self._get_current_mode()
        if mode == "strip":
            processed = strip_line_numbers(raw_text)
        elif mode == "preserve":
            processed = preserve(raw_text)
        else:
            processed = smart(raw_text)

        if getattr(self, "_auto_close", False):
            processed = compensate_auto_close(processed)

        total_chars = len(processed)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text(f"0 / {total_chars} characters")
        self.progress_bar.set_show_text(True)

        prefix = "Typing selection..." if self._is_typing_selection else "Typing..."
        self.set_status(f"{prefix} 0/{total_chars} characters")

        typo_pct = float(self._typo_rate) if self.humanize_toggle.get_active() else 0.0

        self.typing_controller.start(
            text=processed,
            delay_ms=int(self.delay_spin.get_value()),
            on_progress=self._update_progress,
            on_complete=self._on_typing_complete,
            on_cancelled=lambda sent: self._on_typing_cancelled(sent),
            on_error=lambda msg: self._on_typing_error(msg),
            enable_humanize=self.humanize_toggle.get_active(),
            typo_rate_pct=typo_pct,
        )

    def _update_progress(self, sent: int, total: int) -> None:
        fraction = sent / total if total > 0 else 0.0
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{sent} / {total} characters")
        self.progress_bar.set_show_text(True)
        prefix = "Typing selection..." if self._is_typing_selection else "Typing..."
        self.set_status(f"{prefix} {sent}/{total} characters")

    def _on_typing_complete(self, total: int) -> None:
        duration_ms = int((time.monotonic() - self._typing_start_time) * 1000)
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text(f"{total} / {total} characters")
        prefix = "Typed selection of" if self._is_typing_selection else "Typed"

        wpm = 0
        if duration_ms > 0:
            minutes = duration_ms / 60000.0
            wpm = int((total / 5.0) / minutes) if minutes > 0 else 0

        dur_display = f"{duration_ms / 1000:.1f}s" if duration_ms >= 1000 else f"{duration_ms}ms"
        cadence_str = " [Humanized]" if self.humanize_toggle.get_active() else ""
        self.set_status(f"✓ {prefix} {total} chars in {dur_display} ({wpm} WPM){cadence_str}")

        if getattr(self, "_sound_chime", True):
            play_chime()

        self.session_log_store.add(
            char_count=total,
            duration_ms=duration_ms,
            mode=self._get_current_mode(),
            language=self._active_editor().get_language_id(),
            status="complete",
        )
        self._refresh_session_logs()
        self._send_notification(f"Typed {total} chars in {dur_display} ({wpm} WPM)")

        GLib.timeout_add(500, lambda: (self._set_state(AppState.IDLE), False)[1])


    def _on_typing_cancelled(self, sent: int) -> None:
        duration_ms = int((time.monotonic() - self._typing_start_time) * 1000)
        self.set_status(f"⚠ Stopped at {sent} characters.")

        if sent > 0:
            self.session_log_store.add(
                char_count=sent,
                duration_ms=duration_ms,
                mode=self._get_current_mode(),
                language=self._active_editor().get_language_id(),
                status="cancelled",
            )
            self._refresh_session_logs()

        self._set_state(AppState.IDLE)

    def _on_typing_error(self, msg: str) -> None:
        duration_ms = int((time.monotonic() - self._typing_start_time) * 1000)
        self.set_status(f"✗ Error: {msg}")

        self.session_log_store.add(
            char_count=0,
            duration_ms=duration_ms,
            mode=self._get_current_mode(),
            language=self._active_editor().get_language_id(),
            status="error",
        )
        self._refresh_session_logs()

        self._send_notification(f"Typing error: {msg}")
        self._set_state(AppState.IDLE)

    # ═══════════════════════════════════════════════════════
    #  NOTIFICATIONS
    # ═══════════════════════════════════════════════════════

    def _send_notification(self, body: str) -> None:
        """Send a desktop notification if enabled."""
        if not self._notify_on_complete:
            return
        try:
            app = self.get_application()
            if app:
                notif = Gio.Notification.new("CodeWriter")
                notif.set_body(body)
                app.send_notification("codewriter-status", notif)
        except Exception:
            pass

    def set_status(self, text: str) -> None:
        self.status_label.set_text(text)
        if hasattr(self, "status_pill"):
            for cls in (
                "status-pill-ready",
                "status-pill-typing",
                "status-pill-paused",
                "status-pill-armed",
                "status-pill-done",
            ):
                self.status_pill.remove_css_class(cls)

            if self.state == AppState.TYPING:
                self.status_pill.set_text("● Streaming")
                self.status_pill.add_css_class("status-pill-typing")
            elif self.state == AppState.PAUSED:
                self.status_pill.set_text("⏸ Paused")
                self.status_pill.add_css_class("status-pill-paused")
            elif self.state == AppState.COUNTDOWN:
                self.status_pill.set_text("⏳ Armed")
                self.status_pill.add_css_class("status-pill-armed")
            else:
                self.status_pill.set_text("● Ready")
                self.status_pill.add_css_class("status-pill-ready")




# Backward compatibility alias
CodeTyperWindow = CodeWriterWindow


