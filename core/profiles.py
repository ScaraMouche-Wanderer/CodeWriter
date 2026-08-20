"""
Profile storage and management for CodeWriter.
Provides persistent configuration profiles stored as JSON.
Pure data layer with zero UI dependencies.
"""

import json
import os
import shutil
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
    Manages loading and saving user typing profiles to ~/.local/share/codewriter/profiles.json
    using atomic file operations and self-healing error recovery.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        if path:
            self._path = Path(path)
        else:
            new_path = Path.home() / ".local" / "share" / "codewriter" / "profiles.json"
            old_path = Path.home() / ".local" / "share" / "codetyper" / "profiles.json"
            if not new_path.exists() and old_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(old_path, new_path)
                except Exception:
                    pass
            self._path = new_path

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
        Appends or updates a profile by matching 'name'.
        Returns the updated profile list.
        """
        profiles = self.load()
        idx = next((i for i, p in enumerate(profiles) if p.get("name") == profile.get("name")), None)

        if idx is not None:
            profiles[idx] = profile
        else:
            profiles.append(profile)

        self.save(profiles)
        return profiles

    def delete(self, name: str) -> List[dict]:
        """
        Removes the profile with matching 'name'.
        'Default' profile can never be deleted.
        Returns the updated profile list.
        """
        if name == "Default":
            return self.load()

        profiles = [p for p in self.load() if p.get("name") != name]
        self.save(profiles)
        return profiles
