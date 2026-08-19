"""
Unit tests for core.profiles (ProfileStore persistence, upsert, and self-healing).
"""

from pathlib import Path

from core.profiles import DEFAULT_PROFILE, ProfileStore


def test_load_nonexistent_creates_default(tmp_path: Path) -> None:
    """Loading from a non-existent path returns [DEFAULT_PROFILE] and creates the file."""
    profile_path = tmp_path / "codetyper" / "profiles.json"
    store = ProfileStore(profile_path)

    assert not profile_path.exists()
    profiles = store.load()

    assert profiles == [DEFAULT_PROFILE]
    assert profile_path.exists()


def test_load_corrupted_file_repairs_and_returns_default(tmp_path: Path) -> None:
    """Loading from corrupt/malformed JSON falls back to [DEFAULT_PROFILE] and repairs the file."""
    profile_path = tmp_path / "profiles.json"
    profile_path.write_text("{corrupt malformed json content ...", encoding="utf-8")

    store = ProfileStore(profile_path)
    profiles = store.load()

    assert profiles == [DEFAULT_PROFILE]
    # Verify file was repaired with valid JSON
    reloaded = store.load()
    assert reloaded == [DEFAULT_PROFILE]


def test_upsert_appends_new_profile(tmp_path: Path) -> None:
    """Upserting a profile with a new name appends it to the list."""
    profile_path = tmp_path / "profiles.json"
    store = ProfileStore(profile_path)

    new_profile = {
        "name": "GFG C++",
        "target": "",
        "language": "cpp",
        "mode": "preserve",
        "delay_ms": 15,
        "countdown_sec": 5,
    }

    updated = store.upsert(new_profile)
    assert len(updated) == 2
    assert updated[0]["name"] == "Default"
    assert updated[1] == new_profile

    # Verify persistence to disk
    persisted = store.load()
    assert len(persisted) == 2
    assert persisted[1]["name"] == "GFG C++"


def test_upsert_replaces_existing_profile_in_place(tmp_path: Path) -> None:
    """Upserting an existing profile name updates it in-place without reordering."""
    profile_path = tmp_path / "profiles.json"
    store = ProfileStore(profile_path)

    store.upsert({"name": "Custom 1", "delay_ms": 10, "countdown_sec": 2, "mode": "smart", "target": "", "language": ""})
    store.upsert({"name": "Custom 2", "delay_ms": 20, "countdown_sec": 4, "mode": "smart", "target": "", "language": ""})

    initial_list = store.load()
    assert [p["name"] for p in initial_list] == ["Default", "Custom 1", "Custom 2"]

    # Update Custom 1
    updated_custom_1 = {
        "name": "Custom 1",
        "delay_ms": 8,
        "countdown_sec": 1,
        "mode": "preserve",
        "target": "browser",
        "language": "python",
    }
    updated = store.upsert(updated_custom_1)

    assert len(updated) == 3
    assert [p["name"] for p in updated] == ["Default", "Custom 1", "Custom 2"]
    assert updated[1]["delay_ms"] == 8
    assert updated[1]["mode"] == "preserve"
