"""
Main application window for CodeTyper.
Constructs the GTK4 GUI shell with countdown overlay, background typing engine,
STOP button, progress bar, profile persistence, and recent snippets history.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from backend.ydotool import YdotoolBackend
from core.app_state import AppState
from core.profiles import ProfileStore
from core.snippets import SnippetStore
from core.text_processor import preserve, smart
from core.typing_engine import TypingController
from ui.countdown import CountdownOverlay
from ui.dialogs import ConfirmReplaceDialog, ProfileNameDialog
from ui.editor import CodeEditor

PRESET_FAST_MS, PRESET_NORMAL_MS, PRESET_SAFE_MS = 2, 8, 20


class CodeTyperWindow(Gtk.ApplicationWindow):
    """Main window for CodeTyper."""

    def __init__(self, backend: YdotoolBackend = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.backend = backend or YdotoolBackend()
        self.typing_controller = TypingController(self.backend)
        self.profile_store, self.snippet_store = ProfileStore(), SnippetStore()
        self._profiles = self.profile_store.load()
        self._recent_snippets = self.snippet_store.load()
        self.state = AppState.IDLE

        self.set_title("CodeTyper")
        self.set_default_size(700, 600)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, css_classes=["main-container"])
        self.countdown_overlay = CountdownOverlay(self.main_box)
        self.set_child(self.countdown_overlay)

        self._build_ui()
        self._populate_profiles_dropdown()
        self._refresh_recent_snippets()
        self.profile_dropdown.connect("notify::selected", self._on_profile_selected)

    def _build_ui(self) -> None:
        # Profile & Editor & Snippets
        p_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, css_classes=["profile-row"])
        self.profile_dropdown = Gtk.DropDown(hexpand=True)
        self.save_profile_btn = Gtk.Button(label="Save as Profile")
        self.save_profile_btn.connect("clicked", self._on_save_profile_clicked)
        for w in (Gtk.Label(label="Profile:"), self.profile_dropdown, self.save_profile_btn):
            p_row.append(w)

        self.editor = CodeEditor()
        self.recent_expander = Gtk.Expander(label="Recent Snippets (0)", css_classes=["recent-expander"])
        self.recent_listbox = Gtk.ListBox()
        self.recent_listbox.connect("row-activated", self._on_recent_row_activated)
        self.recent_expander.set_child(Gtk.ScrolledWindow(child=self.recent_listbox, css_classes=["recent-scroll"], min_content_height=70))

        # Mode & Delay rows
        m_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, css_classes=["mode-row"])
        self.mode_smart_radio = Gtk.CheckButton(label="Smart", active=True)
        self.mode_preserve_radio = Gtk.CheckButton(label="Preserve", group=self.mode_smart_radio)
        for w in (Gtk.Label(label="Mode:"), self.mode_smart_radio, self.mode_preserve_radio):
            m_row.append(w)

        d_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12, css_classes=["delay-row"])
        self.delay_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment.new(5.0, 0.0, 200.0, 1.0, 5.0, 0.0), digits=0)
        self.countdown_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment.new(3.0, 0.0, 10.0, 1.0, 1.0, 0.0), digits=0)
        for w in (Gtk.Label(label="Delay:"), self.delay_spin, Gtk.Label(label="ms"),
                  Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, hexpand=True),
                  Gtk.Label(label="Countdown:"), self.countdown_spin, Gtk.Label(label="sec")):
            d_row.append(w)

        # Presets, Action, Progress, Status
        pr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8, css_classes=["preset-row"])
        pr_row.append(Gtk.Label(label="Presets:"))
        for lbl, val in [("Fast", PRESET_FAST_MS), ("Normal", PRESET_NORMAL_MS), ("Safe", PRESET_SAFE_MS)]:
            btn = Gtk.Button(label=f"{lbl} ({val}ms)")
            btn.connect("clicked", lambda _, v=val: self.delay_spin.set_value(float(v)))
            pr_row.append(btn)

        a_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["action-row"])
        self.arm_button = Gtk.Button(label="ARM & TYPE", hexpand=True, css_classes=["suggested-action", "arm-button"])
        self.arm_button.connect("clicked", self._on_arm_and_type_clicked)
        self.stop_button = Gtk.Button(label="STOP", hexpand=True, visible=False, css_classes=["destructive-action", "stop-button"])
        self.stop_button.connect("clicked", self._on_stop_clicked)
        a_row.append(self.arm_button)
        a_row.append(self.stop_button)

        self.progress_bar = Gtk.ProgressBar(visible=False, css_classes=["codetyper-progress"])
        s_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0, css_classes=["status-row"])
        self.status_label = Gtk.Label(label="Status: Ready", halign=Gtk.Align.START, hexpand=True)
        s_row.append(self.status_label)

        for s in (p_row, self.editor, self.recent_expander, m_row, d_row, pr_row, a_row, self.progress_bar, s_row):
            self.main_box.append(s)

    def _populate_profiles_dropdown(self, selected_name: str = "Default") -> None:
        names = [p.get("name", "Default") for p in self._profiles]
        self.profile_dropdown.set_model(Gtk.StringList.new(names))
        idx = next((i for i, n in enumerate(names) if n == selected_name), 0)
        self.profile_dropdown.set_selected(idx)

    def _refresh_recent_snippets(self) -> None:
        self._recent_snippets = self.snippet_store.load()
        self.recent_expander.set_label(f"Recent Snippets ({len(self._recent_snippets)})")
        while child := self.recent_listbox.get_first_child():
            self.recent_listbox.remove(child)
        for snip in self._recent_snippets:
            row = Gtk.ListBoxRow(css_classes=["recent-row"])
            row.set_child(Gtk.Label(label=snip.get("title", "Snippet"), halign=Gtk.Align.START, hexpand=True, css_classes=["recent-title"]))
            self.recent_listbox.append(row)

    def _on_recent_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        idx = row.get_index()
        if idx < 0 or idx >= len(self._recent_snippets):
            return
        snip = self._recent_snippets[idx]
        cur_text = self.editor.get_text()
        if cur_text and cur_text != snip["content"]:
            dlg = ConfirmReplaceDialog(parent=self)
            dlg.connect("response", lambda d, r: (d.close(), self.editor.set_text(snip["content"])) if r == Gtk.ResponseType.OK else d.close())
            dlg.present()
        else:
            self.editor.set_text(snip["content"])

    def _on_profile_selected(self, dropdown: Gtk.DropDown, _pspec) -> None:
        idx = dropdown.get_selected()
        if idx == Gtk.INVALID_LIST_POSITION or idx >= len(self._profiles):
            return
        p = self._profiles[idx]
        self.delay_spin.set_value(float(p.get("delay_ms", 5)))
        self.countdown_spin.set_value(float(p.get("countdown_sec", 3)))
        (self.mode_smart_radio if p.get("mode") == "smart" else self.mode_preserve_radio).set_active(True)

    def _on_save_profile_clicked(self, _button: Gtk.Button) -> None:
        idx = self.profile_dropdown.get_selected()
        cur_name = self._profiles[idx]["name"] if idx < len(self._profiles) else "Default"
        dlg = ProfileNameDialog(parent=self, default_name=cur_name)

        def _resp(d, resp):
            if resp == Gtk.ResponseType.OK and (name := d.get_profile_name()):
                self._profiles = self.profile_store.upsert({
                    "name": name, "target": "", "language": "",
                    "mode": "smart" if self.mode_smart_radio.get_active() else "preserve",
                    "delay_ms": int(self.delay_spin.get_value()),
                    "countdown_sec": int(self.countdown_spin.get_value()),
                })
                self._populate_profiles_dropdown(selected_name=name)
            d.close()

        dlg.connect("response", _resp)
        dlg.present()

    def _set_state(self, new_state: AppState) -> None:
        self.state = new_state
        is_idle = (new_state == AppState.IDLE)
        is_active = (new_state in (AppState.COUNTDOWN, AppState.TYPING))
        for w in (self.delay_spin, self.countdown_spin, self.mode_smart_radio,
                  self.mode_preserve_radio, self.profile_dropdown, self.save_profile_btn, self.recent_expander):
            w.set_sensitive(is_idle)
        self.editor.get_view().set_editable(is_idle)
        self.arm_button.set_sensitive(is_idle)
        self.arm_button.set_visible(is_idle)
        self.stop_button.set_sensitive(is_active)
        self.stop_button.set_visible(is_active)
        self.progress_bar.set_visible(is_active)

    def _on_arm_and_type_clicked(self, _button: Gtk.Button) -> None:
        if not self.editor.get_text():
            self.set_status("Editor is empty — nothing to type.")
            return

        self._set_state(AppState.COUNTDOWN)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("0 / 0 characters")
        self.progress_bar.set_show_text(True)

        self.countdown_overlay.start(
            seconds=int(self.countdown_spin.get_value()),
            on_tick=lambda rem: self.set_status(f"Starting in {rem}..."),
            on_complete=self._do_type,
            on_cancel=lambda: (self.set_status("Cancelled."), self._set_state(AppState.IDLE)),
        )

    def _on_stop_clicked(self, _button: Gtk.Button) -> None:
        if self.state == AppState.COUNTDOWN:
            self.countdown_overlay.cancel()
        elif self.state == AppState.TYPING:
            self.typing_controller.cancel()

    def _do_type(self) -> None:
        self._set_state(AppState.TYPING)
        raw_text = self.editor.get_text()
        self.snippet_store.add(raw_text)
        self._refresh_recent_snippets()

        processed = smart(raw_text) if self.mode_smart_radio.get_active() else preserve(raw_text)
        self.typing_controller.start(
            text=processed,
            delay_ms=int(self.delay_spin.get_value()),
            on_progress=self._update_progress,
            on_complete=lambda tot: (self.progress_bar.set_fraction(1.0), self.set_status(f"Typed {tot} characters."), self._set_state(AppState.IDLE)),
            on_cancelled=lambda sent: (self.set_status(f"Stopped at {sent} characters."), self._set_state(AppState.IDLE)),
            on_error=lambda msg: (self.set_status(f"Error: {msg}"), self._set_state(AppState.IDLE)),
        )

    def _update_progress(self, sent: int, total: int) -> None:
        fraction = sent / total if total > 0 else 0.0
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{sent} / {total} characters")
        self.progress_bar.set_show_text(True)
        self.set_status(f"Typing... {sent}/{total} characters")

    def set_status(self, text: str) -> None:
        self.status_label.set_text(f"Status: {text}")
