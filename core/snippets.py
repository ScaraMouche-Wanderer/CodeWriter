"""
Recent snippets store for CodeWriter.
Maintains a local, deduplicated history of recently typed snippets (up to 10).
Pure data layer with zero UI dependencies.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import shutil
from typing import List, Optional
import uuid

MAX_RECENT = 10
MAX_SNIPPET_CHARS = 50_000


class SnippetStore:
    """
    Manages loading and saving recent snippets to ~/.local/share/codewriter/recent.json.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        if path:
            self._path = Path(path)
        else:
            new_path = Path.home() / ".local" / "share" / "codewriter" / "recent.json"
            old_path = Path.home() / ".local" / "share" / "codetyper" / "recent.json"
            if not new_path.exists() and old_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(old_path, new_path)
                except Exception:
                    pass
            self._path = new_path

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
        Atomically writes snippets list to disk.
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
        Inserts snippet at top of recent list, deduplicates by content match,
        derives title, clamps to MAX_RECENT, and saves atomically.
        Snippets exceeding MAX_SNIPPET_CHARS are ignored and not saved.
        """
        if not content or len(content) > MAX_SNIPPET_CHARS:
            return self.load()

        snippets = self.load()
        existing_idx = next((i for i, s in enumerate(snippets) if s.get("content") == content), None)

        if existing_idx is not None:
            snippet = snippets.pop(existing_idx)
            snippet["timestamp"] = datetime.now().isoformat()
            if language:
                snippet["language"] = language
        else:
            snippet = {
                "id": str(uuid.uuid4()),
                "title": self._derive_title(content),
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "language": language,
            }

        snippets.insert(0, snippet)
        snippets = snippets[:MAX_RECENT]
        self.save(snippets)
        return snippets

    def delete(self, snippet_id: str) -> List[dict]:
        """Removes a single snippet by ID and saves to disk."""
        snippets = [s for s in self.load() if s.get("id") != snippet_id]
        self.save(snippets)
        return snippets

    def clear(self) -> List[dict]:
        """Deletes all recent snippets and returns empty list."""
        self.save([])
        return []

    @staticmethod
    def _derive_title(content: str) -> str:
        """Derives a human-readable title from the first non-empty line."""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped[:50] + ("..." if len(stripped) > 50 else "")
        return "Empty Snippet"
