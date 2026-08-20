"""
Settings storage and management for CodeWriter.
Persists application-level preferences across restarts.
Pure data layer with zero UI dependencies.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

DEFAULT_SETTINGS = {
    "window_width": 780,
    "window_height": 640,
    "last_selected_profile": "Default",
    "notify_on_complete": True,
    "show_session_stats": True,
    "humanize_cadence": False,
    "typo_rate": 0,
    "auto_close_compensate": False,
    "enable_tray": True,
    "minimize_to_tray": False,
    "font_size": 11,
    "show_line_numbers": True,
    "word_wrap": False,
    "highlight_current_line": True,
    "sound_chime": True,
    "default_delay_ms": 15,
    "default_countdown_sec": 3,
    "default_mode": "smart",
}




class SettingsStore:
    """
    Manages loading and saving app settings to ~/.local/share/codewriter/settings.json.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        if path:
            self._path = Path(path)
        else:
            new_path = Path.home() / ".local" / "share" / "codewriter" / "settings.json"
            old_path = Path.home() / ".local" / "share" / "codetyper" / "settings.json"
            if not new_path.exists() and old_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(old_path, new_path)
                except Exception:
                    pass
            self._path = new_path

    def load(self) -> dict:
        """
        Loads settings dict from disk, merging with DEFAULT_SETTINGS for any missing keys.
        Returns a fresh copy of DEFAULT_SETTINGS on missing or corrupt file.
        """
        settings = dict(DEFAULT_SETTINGS)

        if not self._path.exists():
            return settings

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception:
            pass

        return settings

    def save(self, settings: dict) -> None:
        """
        Atomically writes settings to disk.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._path)
        except Exception as e:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise e
