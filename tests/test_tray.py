"""
Unit tests for ui.tray (StatusNotifierItem and DBusMenu integration).
"""

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

from ui.tray import DBUSMENU_XML, SNI_XML, CodeWriterTray


def test_introspection_xml_validity() -> None:
    """Verify DBus introspection XML documents parse cleanly without errors."""
    sni_node = gi.repository.Gio.DBusNodeInfo.new_for_xml(SNI_XML)
    assert sni_node is not None
    assert len(sni_node.interfaces) == 1
    assert sni_node.interfaces[0].name == "org.kde.StatusNotifierItem"

    menu_node = gi.repository.Gio.DBusNodeInfo.new_for_xml(DBUSMENU_XML)
    assert menu_node is not None
    assert len(menu_node.interfaces) == 1
    assert menu_node.interfaces[0].name == "com.canonical.dbusmenu"


def test_tray_initial_properties() -> None:
    """Test initial properties and state of CodeWriterTray."""
    tray = CodeWriterTray()
    try:
        assert tray.title == "CodeWriter"
        assert tray.icon_name == "codewriter"
        assert tray.status == "Active"
        assert tray.window_visible is True
        assert tray.state_name == "idle"

        # Check SNI property getter
        prop_id = tray._handle_sni_get_property(None, "", "/StatusNotifierItem", "", "Id")
        assert prop_id is not None
        assert prop_id.unpack() == "codewriter"

        prop_status = tray._handle_sni_get_property(None, "", "/StatusNotifierItem", "", "Status")
        assert prop_status is not None
        assert prop_status.unpack() == "Active"

        prop_icon = tray._handle_sni_get_property(None, "", "/StatusNotifierItem", "", "IconName")
        assert prop_icon is not None
        assert prop_icon.unpack() == "codewriter"
    finally:
        tray.destroy()


def test_tray_state_transitions() -> None:
    """Test state changes in CodeWriterTray."""
    tray = CodeWriterTray()
    try:
        # Countdown / Typing state
        tray.set_state("typing", "Streaming code...")
        assert tray.status == "NeedsAttention"
        assert tray.tooltip_text == "Streaming code..."
        assert tray.state_name == "typing"

        # Paused state
        tray.set_state("paused", "Paused")
        assert tray.status == "NeedsAttention"
        assert tray.tooltip_text == "Paused"
        assert tray.state_name == "paused"

        # Done state
        tray.set_state("done", "Finished")
        assert tray.status == "Active"
        assert tray.tooltip_text == "Finished"

        # Back to idle
        tray.set_state("idle")
        assert tray.status == "Active"
        assert tray.state_name == "idle"
    finally:
        tray.destroy()


def test_tray_menu_items_structure() -> None:
    """Test DBusMenu menu items construction and dynamic labels."""
    tray = CodeWriterTray()
    try:
        tray.set_window_visible(True)
        items = tray._get_menu_items()
        item_dict = {cid: cprops for cid, cprops in items}

        # Item 1 should be Hide when window is visible
        assert 1 in item_dict
        assert item_dict[1]["label"].unpack() == "Hide CodeWriter"

        tray.set_window_visible(False)
        items_hidden = tray._get_menu_items()
        item_dict_hidden = {cid: cprops for cid, cprops in items_hidden}
        assert item_dict_hidden[1]["label"].unpack() == "Show CodeWriter"

        # Check arm, stop, pause, sim, preferences, quit items
        assert 3 in item_dict
        assert 4 in item_dict
        assert 5 in item_dict
        assert 6 in item_dict  # Simulation player
        assert 8 in item_dict  # Preferences
        assert 10 in item_dict  # Quit
    finally:
        tray.destroy()


def test_tray_action_dispatching() -> None:
    """Test dispatching of menu item actions to registered callbacks."""
    called = {}

    def on_toggle():
        called["toggle"] = True

    def on_arm():
        called["arm"] = True

    def on_pause():
        called["pause"] = True

    def on_stop():
        called["stop"] = True

    def on_sim():
        called["sim"] = True

    def on_settings():
        called["settings"] = True

    def on_quit():
        called["quit"] = True

    tray = CodeWriterTray(
        on_toggle_window=on_toggle,
        on_arm=on_arm,
        on_pause_resume=on_pause,
        on_stop=on_stop,
        on_simulation_player=on_sim,
        on_settings=on_settings,
        on_quit=on_quit,
    )
    try:
        tray._dispatch_action(1)
        tray._dispatch_action(3)
        tray._dispatch_action(4)
        tray._dispatch_action(5)
        tray._dispatch_action(6)
        tray._dispatch_action(8)
        tray._dispatch_action(10)

        # Run main context iterations to process GLib.idle_add callbacks
        ctx = GLib.MainContext.default()
        while ctx.pending():
            ctx.iteration(False)

        assert called.get("toggle") is True
        assert called.get("arm") is True
        assert called.get("pause") is True
        assert called.get("stop") is True
        assert called.get("sim") is True
        assert called.get("settings") is True
        assert called.get("quit") is True
    finally:
        tray.destroy()

