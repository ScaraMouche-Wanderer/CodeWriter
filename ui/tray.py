"""
System Tray (StatusNotifierItem) integration for CodeWriter.
Provides a native DBus-based system tray icon compatible with GNOME Shell (via AppIndicator / StatusNotifierItem extension),
KDE Plasma, XFCE, and Wayland desktop bars without GTK3 dependencies.
"""

import logging
import os
from typing import Callable, Optional

import gi

gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib

logger = logging.getLogger("CodeWriter.Tray")

SNI_XML = """
<node>
  <interface name="org.kde.StatusNotifierItem">
    <property name="Category" type="s" access="read"/>
    <property name="Id" type="s" access="read"/>
    <property name="Title" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="WindowId" type="i" access="read"/>
    <property name="IconName" type="s" access="read"/>
    <property name="IconThemePath" type="s" access="read"/>
    <property name="Menu" type="o" access="read"/>
    <property name="ItemIsMenu" type="b" access="read"/>
    <property name="ToolTip" type="(sa(iiay)ss)" access="read"/>
    <method name="ContextMenu">
      <arg type="i" name="x" direction="in"/>
      <arg type="i" name="y" direction="in"/>
    </method>
    <method name="Activate">
      <arg type="i" name="x" direction="in"/>
      <arg type="i" name="y" direction="in"/>
    </method>
    <method name="SecondaryActivate">
      <arg type="i" name="x" direction="in"/>
      <arg type="i" name="y" direction="in"/>
    </method>
    <method name="Scroll">
      <arg type="i" name="delta" direction="in"/>
      <arg type="s" name="orientation" direction="in"/>
    </method>
    <signal name="NewTitle"/>
    <signal name="NewIcon"/>
    <signal name="NewAttentionIcon"/>
    <signal name="NewOverlayIcon"/>
    <signal name="NewToolTip"/>
    <signal name="NewStatus">
      <arg type="s" name="status"/>
    </signal>
  </interface>
</node>
"""

DBUSMENU_XML = """
<node>
  <interface name="com.canonical.dbusmenu">
    <property name="Version" type="u" access="read"/>
    <property name="TextDirection" type="s" access="read"/>
    <property name="Status" type="s" access="read"/>
    <property name="IconThemePath" type="as" access="read"/>
    <method name="GetLayout">
      <arg type="i" name="parentId" direction="in"/>
      <arg type="i" name="recursionDepth" direction="in"/>
      <arg type="as" name="propertyNames" direction="in"/>
      <arg type="u" name="revision" direction="out"/>
      <arg type="(ia{sv}av)" name="layout" direction="out"/>
    </method>
    <method name="GetGroupProperties">
      <arg type="ai" name="ids" direction="in"/>
      <arg type="as" name="propertyNames" direction="in"/>
      <arg type="a(ia{sv})" name="properties" direction="out"/>
    </method>
    <method name="GetProperty">
      <arg type="i" name="id" direction="in"/>
      <arg type="s" name="name" direction="in"/>
      <arg type="v" name="value" direction="out"/>
    </method>
    <method name="Event">
      <arg type="i" name="id" direction="in"/>
      <arg type="s" name="eventId" direction="in"/>
      <arg type="v" name="data" direction="in"/>
      <arg type="u" name="timestamp" direction="in"/>
    </method>
    <method name="EventGroup">
      <arg type="a(isvu)" name="events" direction="in"/>
      <arg type="ai" name="idErrors" direction="out"/>
    </method>
    <method name="AboutToShow">
      <arg type="i" name="id" direction="in"/>
      <arg type="b" name="needUpdate" direction="out"/>
    </method>
    <method name="AboutToShowGroup">
      <arg type="ai" name="ids" direction="in"/>
      <arg type="ai" name="updatesNeeded" direction="out"/>
      <arg type="ai" name="idErrors" direction="out"/>
    </method>
    <signal name="ItemsPropertiesUpdated">
      <arg type="a(ia{sv})" name="updatedProps"/>
      <arg type="a(ias)" name="removedProps"/>
    </signal>
    <signal name="LayoutUpdated">
      <arg type="u" name="revision"/>
      <arg type="i" name="parent"/>
    </signal>
    <signal name="ItemActivationRequested">
      <arg type="i" name="id"/>
      <arg type="u" name="timestamp"/>
    </signal>
  </interface>
</node>
"""


class CodeWriterTray:
    """
    StatusNotifierItem (SNI) system tray controller for CodeWriter over DBus.
    Pure GIO/DBus implementation with zero GTK3 dependencies.
    """

    def __init__(
        self,
        on_toggle_window: Optional[Callable[[], None]] = None,
        on_arm: Optional[Callable[[], None]] = None,
        on_pause_resume: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_simulation_player: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
    ) -> None:
        self.on_toggle_window = on_toggle_window
        self.on_arm = on_arm
        self.on_pause_resume = on_pause_resume
        self.on_stop = on_stop
        self.on_simulation_player = on_simulation_player
        self.on_settings = on_settings
        self.on_quit = on_quit


        self.bus: Optional[Gio.DBusConnection] = None
        self.sni_reg_id: int = 0
        self.menu_reg_id: int = 0
        self.watcher_sub_id: int = 0

        self.status: str = "Active"
        self.icon_name: str = "codewriter"
        self.title: str = "CodeWriter"
        self.tooltip_text: str = "CodeWriter — Keystroke Simulation Utility"
        self.window_visible: bool = True
        self.state_name: str = "idle"
        self.menu_revision: int = 1

        self.icon_theme_path = os.path.expanduser("~/.local/share/icons/hicolor")
        resources_icons = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")
        if os.path.exists(resources_icons):
            self.icon_theme_paths = [self.icon_theme_path, resources_icons]
        else:
            self.icon_theme_paths = [self.icon_theme_path]

        self._sni_info = Gio.DBusNodeInfo.new_for_xml(SNI_XML).interfaces[0]
        self._menu_info = Gio.DBusNodeInfo.new_for_xml(DBUSMENU_XML).interfaces[0]

        self._init_dbus()

    def _init_dbus(self) -> None:
        """Initialize DBus connection and register SNI and MenuBar objects."""
        try:
            self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except Exception as e:
            logger.warning(f"Could not connect to session DBus for tray: {e}")
            return

        try:
            self.sni_reg_id = self.bus.register_object(
                "/StatusNotifierItem",
                self._sni_info,
                self._handle_sni_method,
                self._handle_sni_get_property,
                None,
            )
            self.menu_reg_id = self.bus.register_object(
                "/MenuBar",
                self._menu_info,
                self._handle_menu_method,
                self._handle_menu_get_property,
                None,
            )
        except Exception as e:
            logger.warning(f"Failed to register DBus objects for tray: {e}")
            return

        self._register_with_watcher()

    def _register_with_watcher(self) -> None:
        """Register our SNI object with org.kde.StatusNotifierWatcher if present."""
        if not self.bus:
            return

        try:
            self.bus.call(
                "org.kde.StatusNotifierWatcher",
                "/StatusNotifierWatcher",
                "org.kde.StatusNotifierWatcher",
                "RegisterStatusNotifierItem",
                GLib.Variant("(s)", ("/StatusNotifierItem",)),
                None,
                Gio.DBusCallFlags.NONE,
                1500,
                None,
                self._on_register_complete,
            )
        except Exception as e:
            logger.debug(f"StatusNotifierWatcher registration call failed: {e}")

    def _on_register_complete(self, conn: Gio.DBusConnection, res: Gio.AsyncResult) -> None:
        """Callback when RegisterStatusNotifierItem finishes."""
        try:
            conn.call_finish(res)
            logger.info("Successfully registered CodeWriter with StatusNotifierWatcher")
        except Exception as e:
            logger.debug(f"StatusNotifierWatcher registration finish info: {e}")

    # ── SNI DBus Handlers ──────────────────────────────────────────────────

    def _handle_sni_get_property(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        property_name: str,
    ) -> Optional[GLib.Variant]:
        if property_name == "Category":
            return GLib.Variant("s", "ApplicationStatus")
        elif property_name == "Id":
            return GLib.Variant("s", "codewriter")
        elif property_name == "Title":
            return GLib.Variant("s", self.title)
        elif property_name == "Status":
            return GLib.Variant("s", self.status)
        elif property_name == "WindowId":
            return GLib.Variant("i", 0)
        elif property_name == "IconName":
            return GLib.Variant("s", self.icon_name)
        elif property_name == "IconThemePath":
            return GLib.Variant("s", self.icon_theme_path)
        elif property_name == "Menu":
            return GLib.Variant("o", "/MenuBar")
        elif property_name == "ItemIsMenu":
            return GLib.Variant("b", False)
        elif property_name == "ToolTip":
            # ToolTip signature: (sa(iiay)ss) -> (icon_name, icon_data, title, description)
            return GLib.Variant("(sa(iiay)ss)", (self.icon_name, [], self.title, self.tooltip_text))
        return None

    def _handle_sni_method(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        method_name: str,
        parameters: GLib.Variant,
        invocation: Gio.DBusMethodInvocation,
    ) -> None:
        if method_name in ("Activate", "SecondaryActivate"):
            if self.on_toggle_window:
                GLib.idle_add(self.on_toggle_window)
            invocation.return_value(None)
        elif method_name == "ContextMenu":
            invocation.return_value(None)
        elif method_name == "Scroll":
            invocation.return_value(None)
        else:
            invocation.return_value(None)

    # ── DBusMenu Handlers ──────────────────────────────────────────────────

    def _get_menu_items(self) -> list[tuple[int, dict]]:
        """Construct the list of menu items based on current state."""
        toggle_label = "Hide CodeWriter" if self.window_visible else "Show CodeWriter"

        is_running = self.state_name in ("typing", "countdown", "paused")
        is_paused = self.state_name == "paused"

        items = [
            (1, {"label": GLib.Variant("s", toggle_label), "enabled": GLib.Variant("b", True)}),
            (2, {"type": GLib.Variant("s", "separator")}),
            (
                3,
                {
                    "label": GLib.Variant("s", "⚡ Arm Keystrokes (Ctrl+Enter)"),
                    "enabled": GLib.Variant("b", not is_running),
                },
            ),
            (
                4,
                {
                    "label": GLib.Variant("s", "▶ Resume (Ctrl+Space)" if is_paused else "⏸ Pause (Ctrl+Space)"),
                    "enabled": GLib.Variant("b", is_running),
                },
            ),
            (
                5,
                {
                    "label": GLib.Variant("s", "⏹ Stop Keystrokes (Esc)"),
                    "enabled": GLib.Variant("b", is_running),
                },
            ),
            (
                6,
                {
                    "label": GLib.Variant("s", "🎬 Simulation Visualizer (Ctrl+Shift+P)"),
                    "enabled": GLib.Variant("b", not is_running),
                },
            ),
            (7, {"type": GLib.Variant("s", "separator")}),
            (8, {"label": GLib.Variant("s", "⚙ Preferences (Ctrl+,)"), "enabled": GLib.Variant("b", True)}),
            (9, {"type": GLib.Variant("s", "separator")}),
            (10, {"label": GLib.Variant("s", "❌ Quit CodeWriter"), "enabled": GLib.Variant("b", True)}),
        ]
        return items


    def _handle_menu_get_property(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        property_name: str,
    ) -> Optional[GLib.Variant]:
        if property_name == "Version":
            return GLib.Variant("u", 3)
        elif property_name == "TextDirection":
            return GLib.Variant("s", "ltr")
        elif property_name == "Status":
            return GLib.Variant("s", "normal")
        elif property_name == "IconThemePath":
            return GLib.Variant("as", self.icon_theme_paths)
        return None

    def _handle_menu_method(
        self,
        conn: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface_name: str,
        method_name: str,
        parameters: GLib.Variant,
        invocation: Gio.DBusMethodInvocation,
    ) -> None:
        if method_name == "GetLayout":
            parent_id, recursion_depth, property_names = parameters.unpack()
            items = self._get_menu_items()
            child_variants = []
            for cid, cprops in items:
                child_variants.append(GLib.Variant("(ia{sv}av)", (cid, cprops, [])))
            root_props = {"children-display": GLib.Variant("s", "submenu")}
            layout_variant = GLib.Variant("(ia{sv}av)", (0, root_props, child_variants))
            invocation.return_value(GLib.Variant.new_tuple(GLib.Variant.new_uint32(self.menu_revision), layout_variant))


        elif method_name == "GetGroupProperties":
            ids, property_names = parameters.unpack()
            items_dict = {cid: cprops for cid, cprops in self._get_menu_items()}
            results = []
            for item_id in ids:
                if item_id == 0:
                    results.append((0, {"children-display": GLib.Variant("s", "submenu")}))
                elif item_id in items_dict:
                    results.append((item_id, items_dict[item_id]))
            invocation.return_value(GLib.Variant("(a(ia{sv}))", (results,)))

        elif method_name == "GetProperty":
            item_id, name = parameters.unpack()
            items_dict = {cid: cprops for cid, cprops in self._get_menu_items()}
            if item_id in items_dict and name in items_dict[item_id]:
                invocation.return_value(GLib.Variant("(v)", (items_dict[item_id][name],)))
            else:
                invocation.return_value(GLib.Variant("(v)", (GLib.Variant("s", ""),)))

        elif method_name == "Event":
            item_id, event_id, data, timestamp = parameters.unpack()
            if event_id == "clicked":
                self._dispatch_action(item_id)
            invocation.return_value(None)

        elif method_name == "EventGroup":
            events = parameters.unpack()[0]
            for item_id, event_id, data, timestamp in events:
                if event_id == "clicked":
                    self._dispatch_action(item_id)
            invocation.return_value(GLib.Variant("(ai)", ([],)))

        elif method_name == "AboutToShow":
            invocation.return_value(GLib.Variant("(b)", (False,)))

        elif method_name == "AboutToShowGroup":
            invocation.return_value(GLib.Variant("(aiai)", ([], [])))

        else:
            invocation.return_value(None)

    def _dispatch_action(self, item_id: int) -> None:
        """Dispatch menu click actions to registered application handlers."""
        if item_id == 1:
            if self.on_toggle_window:
                GLib.idle_add(self.on_toggle_window)
        elif item_id == 3:
            if self.on_arm:
                GLib.idle_add(self.on_arm)
        elif item_id == 4:
            if self.on_pause_resume:
                GLib.idle_add(self.on_pause_resume)
        elif item_id == 5:
            if self.on_stop:
                GLib.idle_add(self.on_stop)
        elif item_id == 6:
            if self.on_simulation_player:
                GLib.idle_add(self.on_simulation_player)
        elif item_id == 8:
            if self.on_settings:
                GLib.idle_add(self.on_settings)
        elif item_id == 10:
            if self.on_quit:
                GLib.idle_add(self.on_quit)


    # ── Public State Update Methods ────────────────────────────────────────

    def set_state(self, state_name: str, tooltip: Optional[str] = None) -> None:
        """
        Update tray state, icon, and tooltip text.
        state_name can be 'idle', 'countdown', 'typing', 'paused', 'done', 'error'.
        """
        self.state_name = state_name

        if state_name in ("typing", "countdown"):
            self.status = "NeedsAttention"
            self.icon_name = "codewriter"
            self.tooltip_text = tooltip or "CodeWriter — Keystroke Streaming Active"
        elif state_name == "paused":
            self.status = "NeedsAttention"
            self.icon_name = "codewriter"
            self.tooltip_text = tooltip or "CodeWriter — Keystroke Streaming Paused"
        elif state_name == "done":
            self.status = "Active"
            self.icon_name = "codewriter"
            self.tooltip_text = tooltip or "CodeWriter — Keystrokes Completed"
        else:
            self.status = "Active"
            self.icon_name = "codewriter"
            self.tooltip_text = tooltip or "CodeWriter — Ready"

        self._emit_sni_signals()
        self._notify_menu_changed()

    def set_window_visible(self, visible: bool) -> None:
        """Update window visibility state and notify menu update."""
        if self.window_visible != visible:
            self.window_visible = visible
            self._notify_menu_changed()

    def _emit_sni_signals(self) -> None:
        """Emit DBus signals for SNI property updates."""
        if not self.bus or not self.sni_reg_id:
            return
        try:
            self.bus.emit_signal(
                None,
                "/StatusNotifierItem",
                "org.kde.StatusNotifierItem",
                "NewIcon",
                None,
            )
            self.bus.emit_signal(
                None,
                "/StatusNotifierItem",
                "org.kde.StatusNotifierItem",
                "NewStatus",
                GLib.Variant("(s)", (self.status,)),
            )
            self.bus.emit_signal(
                None,
                "/StatusNotifierItem",
                "org.kde.StatusNotifierItem",
                "NewToolTip",
                None,
            )
        except Exception as e:
            logger.debug(f"Failed to emit SNI signals: {e}")

    def _notify_menu_changed(self) -> None:
        """Increment revision and emit LayoutUpdated signal for DBusMenu."""
        if not self.bus or not self.menu_reg_id:
            return
        self.menu_revision += 1
        try:
            self.bus.emit_signal(
                None,
                "/MenuBar",
                "com.canonical.dbusmenu",
                "LayoutUpdated",
                GLib.Variant("(ui)", (self.menu_revision, 0)),
            )
        except Exception as e:
            logger.debug(f"Failed to emit LayoutUpdated signal: {e}")

    def destroy(self) -> None:
        """Unregister DBus objects and clean up."""
        if self.bus:
            if self.sni_reg_id:
                try:
                    self.bus.unregister_object(self.sni_reg_id)
                except Exception:
                    pass
                self.sni_reg_id = 0
            if self.menu_reg_id:
                try:
                    self.bus.unregister_object(self.menu_reg_id)
                except Exception:
                    pass
                self.menu_reg_id = 0
            self.bus = None
