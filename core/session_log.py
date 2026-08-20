"""
Session log store for CodeWriter.
Tracks per-typing-session stats: char count, duration, WPM, mode, language, status.
Pure data layer with zero UI dependencies.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from typing import List, Optional

MAX_SESSION_LOG = 50


class SessionLogStore:
    """
    Manages loading and saving typing session logs to ~/.local/share/codewriter/sessions.json.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        if path:
            self._path = Path(path)
        else:
            new_path = Path.home() / ".local" / "share" / "codewriter" / "sessions.json"
            old_path = Path.home() / ".local" / "share" / "codetyper" / "sessions.json"
            if not new_path.exists() and old_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(old_path, new_path)
                except Exception:
                    pass
            self._path = new_path

    def load(self) -> List[dict]:
        """
        Returns list of session log dicts, most-recent-first.
        Missing or corrupt file returns [] without modifying disk.
        """
        if not self._path.exists():
            return []

        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass

        return []

    def save(self, sessions: List[dict]) -> None:
        """
        Atomically writes sessions list to disk.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(sessions, f, indent=2)
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

    def add(
        self,
        char_count: int,
        duration_ms: int,
        mode: str,
        language: str,
        status: str = "complete",
    ) -> List[dict]:
        """
        Calculates WPM, prepends new session log entry, clamps to MAX_SESSION_LOG,
        and saves atomically.
        """
        # Calculate WPM: (chars / 5) / (duration in minutes)
        wpm = 0
        if duration_ms > 0 and char_count > 0:
            minutes = duration_ms / 60000.0
            wpm = int((char_count / 5.0) / minutes) if minutes > 0 else 0

        session = {
            "timestamp": datetime.now().isoformat(),
            "char_count": char_count,
            "duration_ms": duration_ms,
            "wpm": wpm,
            "mode": mode,
            "language": language,
            "status": status,
        }

        sessions = self.load()
        sessions.insert(0, session)
        sessions = sessions[:MAX_SESSION_LOG]
        self.save(sessions)
        return sessions

    def clear(self) -> None:
        """Deletes all session logs."""
        self.save([])
