"""
Keyboard shortcuts window for CodeTyper.
Displays all available shortcuts grouped by section using Gtk.ShortcutsWindow.
"""

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


def create_shortcuts_window(parent: Gtk.Window) -> Gtk.ShortcutsWindow:
    """
    Build and return a Gtk.ShortcutsWindow showing all CodeTyper shortcuts.
    """
    win = Gtk.ShortcutsWindow(transient_for=parent, modal=True)

    section = Gtk.ShortcutsSection(title="CodeWriter Shortcuts", section_name="main")
    section.set_visible(True)

    # ── Typing & Simulation ──
    typing_group = Gtk.ShortcutsGroup(title="Typing & Simulation")
    typing_group.set_visible(True)
    _add_shortcut(typing_group, "<Control>Return", "ARM & TYPE")
    _add_shortcut(typing_group, "Space", "Pause / Resume Typing")
    _add_shortcut(typing_group, "Escape", "Stop / Cancel Countdown")
    _add_shortcut(typing_group, "<Control>p", "Pre-Flight Preview")
    _add_shortcut(typing_group, "<Control><Shift>p", "Live Simulation Visualizer")
    section.append(typing_group)

    # ── Editor & Line Tools ──
    editor_group = Gtk.ShortcutsGroup(title="Editor & Tools")
    editor_group.set_visible(True)
    _add_shortcut(editor_group, "<Control><Shift>f", "Auto Format Code (JSON/SQL/HTML)")
    _add_shortcut(editor_group, "<Control>m", "Extract Code from AI Markdown")
    _add_shortcut(editor_group, "<Control><Shift>d", "Duplicate Line / Selection")
    _add_shortcut(editor_group, "<Control><Shift>k", "Delete Line")
    _add_shortcut(editor_group, "<Alt>Up", "Move Line Up")
    _add_shortcut(editor_group, "<Alt>Down", "Move Line Down")
    _add_shortcut(editor_group, "<Alt>z", "Toggle Word Wrap")
    _add_shortcut(editor_group, "<Control>plus", "Zoom In Font")
    _add_shortcut(editor_group, "<Control>minus", "Zoom Out Font")
    _add_shortcut(editor_group, "<Control>0", "Reset Font Zoom")
    _add_shortcut(editor_group, "<Control>f", "Find")
    _add_shortcut(editor_group, "<Control>h", "Find & Replace")
    _add_shortcut(editor_group, "<Control>o", "Open File")
    _add_shortcut(editor_group, "<Control>s", "Save File")
    _add_shortcut(editor_group, "<Control>l", "Clear Editor")
    section.append(editor_group)

    # ── Speed Presets ──
    preset_group = Gtk.ShortcutsGroup(title="Speed Presets")
    preset_group.set_visible(True)
    _add_shortcut(preset_group, "<Control>1", "Fast (2ms)")
    _add_shortcut(preset_group, "<Control>2", "Normal (8ms)")
    _add_shortcut(preset_group, "<Control>3", "Safe (20ms)")
    section.append(preset_group)

    # ── Application ──
    app_group = Gtk.ShortcutsGroup(title="Application")
    app_group.set_visible(True)
    _add_shortcut(app_group, "<Control>comma", "Preferences")
    _add_shortcut(app_group, "<Control>question", "Show Shortcuts")
    section.append(app_group)


    win.add_section(section)
    return win


def _add_shortcut(group: Gtk.ShortcutsGroup, accelerator: str, title: str) -> None:
    """Helper to add a Gtk.ShortcutsShortcut to a group."""
    shortcut = Gtk.ShortcutsShortcut(
        accelerator=accelerator,
        title=title,
    )
    shortcut.set_visible(True)
    group.append(shortcut)
