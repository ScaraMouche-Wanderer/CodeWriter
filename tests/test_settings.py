"""
Unit tests for core.settings (SettingsStore persistence, fallback, and partial merge).
"""

from pathlib import Path

from core.settings import DEFAULT_SETTINGS, SettingsStore


def test_missing_settings_file_returns_defaults(tmp_path: Path) -> None:
    """Missing settings file returns DEFAULT_SETTINGS."""
    settings_file = tmp_path / "settings.json"
    store = SettingsStore(settings_file)

    loaded = store.load()
    assert loaded == DEFAULT_SETTINGS


def test_corrupted_settings_file_returns_defaults(tmp_path: Path) -> None:
    """Corrupted settings file returns DEFAULT_SETTINGS without raising."""
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{invalid json...", encoding="utf-8")
    store = SettingsStore(settings_file)

    loaded = store.load()
    assert loaded == DEFAULT_SETTINGS


def test_partial_settings_file_merges_with_defaults(tmp_path: Path) -> None:
    """Partial settings file merges with DEFAULT_SETTINGS for missing keys."""
    settings_file = tmp_path / "settings.json"
    store = SettingsStore(settings_file)

    # Save only window_width
    store.save({"window_width": 950})

    loaded = store.load()
    assert loaded["window_width"] == 950
    assert loaded["window_height"] == DEFAULT_SETTINGS["window_height"]
    assert loaded["last_selected_profile"] == DEFAULT_SETTINGS["last_selected_profile"]


def test_save_and_reload_settings(tmp_path: Path) -> None:
    """Settings saved to disk are accurately reloaded."""
    settings_file = tmp_path / "settings.json"
    store = SettingsStore(settings_file)

    custom = {
        "window_width": 880,
        "window_height": 720,
        "last_selected_profile": "GFG C++",
    }
    store.save(custom)

    loaded = store.load()
    assert loaded == custom
