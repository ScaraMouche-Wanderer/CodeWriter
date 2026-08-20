import gi
gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk

from ui.editor import CodeEditor, SUPPORTED_LANGUAGES


def test_code_editor_initial_state() -> None:
    """New CodeEditor has empty buffer and zeroed stats."""
    editor = CodeEditor()
    assert editor.get_text() == ""
    assert editor.get_selected_text() is None
    assert editor.get_stats() == {
        "lines": 0,
        "chars": 0,
        "words": 0,
        "cursor_line": 1,
        "cursor_col": 1,
        "selected_chars": 0,
    }



def test_code_editor_set_text_and_stats() -> None:
    """Setting text updates buffer, lines, and character counts."""
    editor = CodeEditor()
    editor.set_text("def hello():\n    return 42\n")
    stats = editor.get_stats()
    assert stats["lines"] == 3
    assert stats["chars"] == 27
    assert stats["selected_chars"] == 0


def test_code_editor_selection_bounds() -> None:
    """Selecting text correctly returns substring and updates selected_chars."""
    editor = CodeEditor()
    editor.set_text("print('hello')\nprint('world')")
    buf = editor.get_buffer()

    # No selection
    assert editor.get_selected_text() is None
    assert editor.get_stats()["selected_chars"] == 0

    # Select first line
    start_iter = buf.get_start_iter()
    end_iter = buf.get_iter_at_offset(14)
    buf.select_range(start_iter, end_iter)

    assert editor.get_selected_text() == "print('hello')"
    assert editor.get_stats()["selected_chars"] == 14


def test_code_editor_language_setting() -> None:
    """Setting supported language updates current_lang_id without error."""
    editor = CodeEditor()
    assert editor.get_language_id() == "plain"

    for _, lang_id in SUPPORTED_LANGUAGES:
        editor.set_language(lang_id)
        assert editor.get_language_id() == lang_id
