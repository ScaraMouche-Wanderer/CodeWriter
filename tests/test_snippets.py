"""
Unit tests for core.snippets (SnippetStore, dedup, title derivation, and capping).
"""

from pathlib import Path
import time

from core.snippets import SnippetStore


def test_add_snippet_to_empty_store(tmp_path: Path) -> None:
    """Adding a snippet to an empty store results in a 1-item list."""
    store_path = tmp_path / "recent.json"
    store = SnippetStore(store_path)

    assert store.load() == []
    updated = store.add("print('hello world')")

    assert len(updated) == 1
    assert updated[0]["content"] == "print('hello world')"
    assert updated[0]["title"] == "print('hello world')"
    assert "id" in updated[0]
    assert "timestamp" in updated[0]


def test_duplicate_snippet_moves_to_top_not_duplicated(tmp_path: Path) -> None:
    """Adding the same content twice results in exactly 1 item with updated timestamp."""
    store_path = tmp_path / "recent.json"
    store = SnippetStore(store_path)

    store.add("snippet A")
    time.sleep(0.01)
    store.add("snippet B")
    time.sleep(0.01)

    initial = store.load()
    assert [s["content"] for s in initial] == ["snippet B", "snippet A"]
    initial_a_time = next(s["timestamp"] for s in initial if s["content"] == "snippet A")

    # Re-add snippet A
    time.sleep(0.01)
    updated = store.add("snippet A")
    assert len(updated) == 2
    assert [s["content"] for s in updated] == ["snippet A", "snippet B"]
    updated_a_time = updated[0]["timestamp"]
    assert updated_a_time > initial_a_time


def test_max_recent_cap_at_10(tmp_path: Path) -> None:
    """Adding 12 distinct snippets results in exactly 10 items, oldest dropped."""
    store_path = tmp_path / "recent.json"
    store = SnippetStore(store_path)

    for i in range(12):
        store.add(f"snippet {i}")

    snippets = store.load()
    assert len(snippets) == 10
    # Most recent first: snippet 11 down to snippet 2
    assert snippets[0]["content"] == "snippet 11"
    assert snippets[-1]["content"] == "snippet 2"


def test_title_derivation_multiline_and_long_line(tmp_path: Path) -> None:
    """Title correctly skips blank leading lines and truncates lines > 50 characters."""
    store_path = tmp_path / "recent.json"
    store = SnippetStore(store_path)

    # Blank leading lines
    multiline = "\n\n   \n    class Solution:\n        pass"
    store.add(multiline)
    snippets = store.load()
    assert snippets[0]["title"] == "class Solution:"

    # Long line (> 50 chars)
    long_line = "a" * 80
    store.add(long_line)
    snippets = store.load()
    assert len(snippets[0]["title"]) == 53  # 50 chars + "..."
    assert snippets[0]["title"].endswith("...")


def test_missing_or_corrupt_file_returns_empty_list(tmp_path: Path) -> None:
    """Loading from missing or corrupt file returns [] without raising."""
    nonexistent = tmp_path / "missing.json"
    store = SnippetStore(nonexistent)
    assert store.load() == []
    assert not nonexistent.exists()

    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{bad json...", encoding="utf-8")
    corrupt_store = SnippetStore(corrupt)
    assert corrupt_store.load() == []
