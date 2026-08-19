"""
Settings storage and management for CodeTyper.
Persists application-level preferences across restarts.
Pure data layer with zero UI dependencies.
"""

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_SETTINGS = {
    "window_width": 700,
    "window_height": 600,
    "last_selected_profile": "Default",
}


class SettingsStore:
    """
    Manages loading and saving app settings to ~/.local/share/codetyper/settings.json.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else (Path.home() / ".local" / "share" / "codetyper" / "settings.json")

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
