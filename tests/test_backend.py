"""
Unit tests for backend.ydotool (YdotoolBackend health checks, caching, and retry logic).
"""

from unittest.mock import MagicMock, patch
import pytest
import subprocess
import time

from backend.ydotool import BackendUnavailableError, YdotoolBackend


def test_is_available_caching_and_force() -> None:
    """Test is_available caches result for TTL and force=True bypasses cache."""
    backend = YdotoolBackend(cache_ttl=0.2)

    call_count = 0

    def mock_check():
        nonlocal call_count
        call_count += 1
        return True, ""

    backend._check_availability = mock_check

    # First call - performs check
    res1 = backend.is_available()
    assert res1 == (True, "")
    assert call_count == 1

    # Second call within TTL - uses cache
    res2 = backend.is_available()
    assert res2 == (True, "")
    assert call_count == 1

    # Force call - bypasses cache
    res3 = backend.is_available(force=True)
    assert res3 == (True, "")
    assert call_count == 2

    # Wait for TTL to expire
    time.sleep(0.25)
    res4 = backend.is_available()
    assert res4 == (True, "")
    assert call_count == 3


def test_type_text_success_immediate() -> None:
    """Test type_text succeeds on first attempt without retrying."""
    backend = YdotoolBackend()

    mock_run = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""))
    with patch("subprocess.run", mock_run):
        backend.type_text("hello", delay_ms=5)

    assert mock_run.call_count == 1


def test_type_text_retry_recovers() -> None:
    """Test type_text retries once on transient non-zero returncode and succeeds."""
    backend = YdotoolBackend()

    fail_res = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="daemon busy")
    succ_res = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    mock_run = MagicMock(side_effect=[fail_res, succ_res])
    with patch("subprocess.run", mock_run), patch("time.sleep") as mock_sleep:
        backend.type_text("code chunk", delay_ms=5)

    assert mock_run.call_count == 2
    assert mock_sleep.call_count == 1


def test_type_text_retry_fails_eventually() -> None:
    """Test type_text raises BackendUnavailableError when retry also fails."""
    backend = YdotoolBackend()

    fail_res = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="connection refused")

    mock_run = MagicMock(return_value=fail_res)
    with patch("subprocess.run", mock_run), patch("time.sleep"):
        with pytest.raises(BackendUnavailableError) as exc_info:
            backend.type_text("failing text", delay_ms=5)

    assert mock_run.call_count == 2
    assert "connection refused" in str(exc_info.value)


def test_type_text_file_not_found_no_retry() -> None:
    """Test FileNotFoundError fails immediately without retry."""
    backend = YdotoolBackend()

    mock_run = MagicMock(side_effect=FileNotFoundError("No such file"))
    with patch("subprocess.run", mock_run), patch("time.sleep") as mock_sleep:
        with pytest.raises(BackendUnavailableError) as exc_info:
            backend.type_text("test", delay_ms=5)

    assert mock_run.call_count == 1
    assert mock_sleep.call_count == 0
    assert "not found in PATH" in str(exc_info.value)


def test_send_backspace():
    backend = YdotoolBackend()
    mock_run = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""))
    with patch("subprocess.run", mock_run):
        backend.send_backspace(count=2, delay_ms=5)

    assert mock_run.call_count == 1
    args = mock_run.call_args[0][0]
    assert "14:1" in args
    assert "14:0" in args

