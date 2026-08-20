"""Unit tests for core.templates module."""

from core.templates import STARTER_TEMPLATES, get_all_templates, get_templates_for_language


def test_starter_templates_presence():
    templates = get_all_templates()
    assert len(templates) >= 8
    langs = {t.language_id for t in templates}
    assert "python" in langs
    assert "cpp" in langs
    assert "java" in langs
    assert "rust" in langs
    assert "go" in langs


def test_get_templates_for_language():
    py_tmpls = get_templates_for_language("python")
    assert len(py_tmpls) >= 2
    for t in py_tmpls:
        assert t.language_id == "python"
        assert len(t.content) > 0
