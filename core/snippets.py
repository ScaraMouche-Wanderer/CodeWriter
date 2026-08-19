"""
Recent snippets store for CodeTyper.
Maintains a local, deduplicated history of recently typed snippets (up to 10).
Pure data layer with zero UI dependencies.
"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import List, Optional
import uuid

MAX_RECENT = 10


class SnippetStore:
    """
    Manages loading and saving recent snippets to ~/.local/share/codetyper/recent.json.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else (Path.home() / ".local" / "share" / "codetyper" / "recent.json")

    def load(self) -> List[dict]:
        """
        Returns list of snippet dicts, most-recent-first.
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

    def save(self, snippets: List[dict]) -> None:
        """
        Atomically writes snippet list to disk.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")

        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(snippets, f, indent=2)
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

    def add(self, content: str, language: str = "") -> List[dict]:
        """
        Adds a new snippet entry, handling deduplication and the 10-item cap.
        """
        snippets = self.load()

        # 1. Deduplicate by exact content match (remove existing to move-to-top)
        snippets = [s for s in snippets if s.get("content") != content]

        # 2. Derive title from first non-empty line
        title = "(empty snippet)"
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped:
                title = stripped[:50] + ("..." if len(stripped) > 50 else "")
                break

        # 3. Create entry and prepend
        new_entry = {
            "id": uuid.uuid4().hex,
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "language": language,
            "content": content,
        }
        snippets.insert(0, new_entry)

        # 4. Truncate to MAX_RECENT
        snippets = snippets[:MAX_RECENT]

        self.save(snippets)
        return snippets
