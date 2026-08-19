"""
Profile storage and management for CodeTyper.
Provides persistent configuration profiles stored as JSON.
Pure data layer with zero UI dependencies.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

DEFAULT_PROFILE = {
    "name": "Default",
    "target": "",
    "language": "",
    "mode": "smart",  # "smart" | "preserve"
    "delay_ms": 5,
    "countdown_sec": 3,
}


class ProfileStore:
    """
    Manages loading and saving user typing profiles to ~/.local/share/codetyper/profiles.json
    using atomic file operations and self-healing error recovery.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else (Path.home() / ".local" / "share" / "codetyper" / "profiles.json")

    def load(self) -> List[dict]:
        """
        Returns list of profile dicts.
        If file doesn't exist or contains invalid JSON, falls back to [DEFAULT_PROFILE]
        and writes it back to disk (self-healing).
        """
        if not self._path.exists():
            default_list = [dict(DEFAULT_PROFILE)]
            self.save(default_list)
            return default_list

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    return data
        except Exception:
            pass

        # Self-heal on corrupt or malformed file
        default_list = [dict(DEFAULT_PROFILE)]
        self.save(default_list)
        return default_list

    def save(self, profiles: List[dict]) -> None:
        """
        Atomically writes the full profile list to disk.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=2)
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

    def upsert(self, profile: dict) -> List[dict]:
        """
        Loads current profiles, replaces matching entry (by name) in-place or appends,
        saves to disk, and returns the updated list.
        """
        profiles = self.load()
        target_name = profile.get("name", "Default")

        for idx, existing in enumerate(profiles):
            if existing.get("name") == target_name:
                profiles[idx] = dict(profile)
                self.save(profiles)
                return profiles

        profiles.append(dict(profile))
        self.save(profiles)
        return profiles
