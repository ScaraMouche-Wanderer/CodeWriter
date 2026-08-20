"""
Unit tests for extended CodeEditor features (font zooming, word wrap, and line manipulation).
"""

from ui.editor import CodeEditor


def test_editor_font_zooming() -> None:
    """Test zooming in, zooming out, and resetting font size."""
    editor = CodeEditor()
    assert editor.get_font_size() == 11

    # Zoom in
    assert editor.zoom_in() == 12
    assert editor.zoom_in() == 13
    assert editor.get_font_size() == 13

    # Zoom out
    assert editor.zoom_out() == 12
    assert editor.get_font_size() == 12

    # Reset
    assert editor.reset_zoom() == 11
    assert editor.get_font_size() == 11


def test_editor_word_wrap() -> None:
    """Test toggling and setting word wrap on CodeEditor."""
    editor = CodeEditor()
    assert editor.is_word_wrap_enabled() is False

    assert editor.toggle_word_wrap() is True
    assert editor.is_word_wrap_enabled() is True

    assert editor.toggle_word_wrap() is False
    assert editor.is_word_wrap_enabled() is False

    editor.set_word_wrap(True)
    assert editor.is_word_wrap_enabled() is True


def test_editor_line_duplication() -> None:
    """Test duplicating the current line in CodeEditor."""
    editor = CodeEditor()
    editor.set_text("line 1\nline 2\nline 3")

    # Place cursor at start
    res = editor.get_buffer().get_iter_at_line(0)
    start_iter = res[1] if isinstance(res, tuple) else res
    editor.get_buffer().place_cursor(start_iter)

    editor.duplicate_current_line_or_selection()
    text = editor.get_text()
    assert text.startswith("line 1\nline 1\n")


def test_editor_line_deletion() -> None:
    """Test deleting the current line under cursor."""
    editor = CodeEditor()
    editor.set_text("alpha\nbeta\ngamma")

    # Delete line 1 (beta)
    res = editor.get_buffer().get_iter_at_line(1)
    iter_beta = res[1] if isinstance(res, tuple) else res
    editor.get_buffer().place_cursor(iter_beta)

    editor.delete_current_line()
    text = editor.get_text().strip()
    assert "beta" not in text
    assert "alpha" in text
    assert "gamma" in text

