from core.humanizer import (
    calculate_char_delay,
    estimate_typing_duration,
    get_typo_character,
    should_trigger_typo,
)


def test_calculate_char_delay_disabled():
    delay = calculate_char_delay(base_delay_ms=10.0, char="a", enable_humanize=False)
    assert delay == 10.0


def test_calculate_char_delay_jitter_range():
    base = 10.0
    for _ in range(50):
        d = calculate_char_delay(base_delay_ms=base, char="a", jitter_pct=25.0, enable_humanize=True)
        # Should be within +/- 25% for regular characters
        assert 7.0 <= d <= 13.0


def test_calculate_char_delay_boundary_pause():
    base = 10.0
    newline_delay = calculate_char_delay(base_delay_ms=base, char="\n", enable_humanize=True)
    assert newline_delay > base  # newline pause adds 40-100ms

    delim_delay = calculate_char_delay(base_delay_ms=base, char=";", enable_humanize=True)
    assert delim_delay > base  # semicolon pause adds 15-35ms


def test_estimate_typing_duration():
    text = "hello world\n" * 10  # 120 chars
    dur_sec, wpm = estimate_typing_duration(text, base_delay_ms=10.0, enable_humanize=False)
    assert dur_sec == 1.2
    assert wpm > 0

    dur_human, wpm_human = estimate_typing_duration(text, base_delay_ms=10.0, enable_humanize=True)
    assert dur_human > dur_sec  # human pauses increase duration
    assert wpm_human < wpm

    dur_typo, _ = estimate_typing_duration(text, base_delay_ms=10.0, enable_humanize=True, typo_rate_pct=100.0)
    assert dur_typo > dur_human


def test_get_typo_character():
    # Lowercase neighbor
    typo_a = get_typo_character("a")
    assert typo_a in ["s", "q", "w", "z"]

    # Uppercase neighbor preserves case
    typo_A = get_typo_character("A")
    assert typo_A in ["S", "Q", "W", "Z"]

    # Non-letter or whitespace returns None
    assert get_typo_character("\n") is None
    assert get_typo_character("") is None


def test_should_trigger_typo():
    assert not should_trigger_typo("a", 0.0)
    assert not should_trigger_typo("\n", 50.0)
    assert should_trigger_typo("a", 100.0)

