"""
Human typing cadence and jitter simulation module for CodeTyper.
Provides realistic keystroke timing variation and natural punctuation pauses
to simulate human typing rhythms and avoid robotic fixed-interval detection.
"""

import random
from typing import Optional, Tuple

# Physical QWERTY keyboard adjacent key map for realistic human typo simulation
QWERTY_NEIGHBORS: dict[str, list[str]] = {
    "a": ["s", "q", "w", "z"],
    "b": ["v", "g", "h", "n"],
    "c": ["x", "d", "f", "v"],
    "d": ["s", "e", "r", "f", "x", "c"],
    "e": ["w", "s", "d", "r", "3", "4"],
    "f": ["d", "r", "t", "g", "c", "v"],
    "g": ["f", "t", "y", "h", "v", "b"],
    "h": ["g", "y", "u", "j", "b", "n"],
    "i": ["u", "j", "k", "o", "8", "9"],
    "j": ["h", "u", "i", "k", "n", "m"],
    "k": ["j", "i", "o", "l", "m"],
    "l": ["k", "o", "p", ";"],
    "m": ["n", "j", "k"],
    "n": ["b", "h", "j", "m"],
    "o": ["i", "k", "l", "p", "9", "0"],
    "p": ["o", "l", "[", "-", "0"],
    "q": ["1", "2", "w", "a"],
    "r": ["e", "d", "f", "t", "4", "5"],
    "s": ["a", "w", "e", "d", "z", "x"],
    "t": ["r", "f", "g", "y", "5", "6"],
    "u": ["y", "h", "j", "i", "7", "8"],
    "v": ["c", "f", "g", "b"],
    "w": ["q", "a", "s", "e", "2", "3"],
    "x": ["z", "s", "d", "c"],
    "y": ["t", "g", "h", "u", "6", "7"],
    "z": ["a", "s", "x"],
    "0": ["9", "-", "p"],
    "1": ["2", "q"],
    "2": ["1", "3", "q", "w"],
    "3": ["2", "4", "w", "e"],
    "4": ["3", "5", "e", "r"],
    "5": ["4", "6", "r", "t"],
    "6": ["5", "7", "t", "y"],
    "7": ["6", "8", "y", "u"],
    "8": ["7", "9", "u", "i"],
    "9": ["8", "0", "i", "o"],
}


def get_typo_character(char: str) -> Optional[str]:
    """
    Returns a plausible neighbor character for a given alphanumeric character.
    Preserves case if original was uppercase. Returns None if no neighbor exists.
    """
    if not char or len(char) != 1:
        return None

    lower_char = char.lower()
    neighbors = QWERTY_NEIGHBORS.get(lower_char)
    if not neighbors:
        return None

    mistake = random.choice(neighbors)
    if char.isupper():
        return mistake.upper()
    return mistake


def should_trigger_typo(char: str, typo_rate_pct: float) -> bool:
    """
    Determines whether a typo should occur on this character.
    Typos only occur on alphanumeric characters (not on whitespace or control chars).
    """
    if typo_rate_pct <= 0.0 or not char or not char.isalnum():
        return False
    return random.uniform(0.0, 100.0) < typo_rate_pct


def calculate_char_delay(
    base_delay_ms: float,
    char: str,
    prev_char: str = "",
    jitter_pct: float = 25.0,
    enable_humanize: bool = True,
) -> float:
    """
    Calculate the delay in milliseconds for typing a given character.

    Args:
        base_delay_ms: Base keystroke delay in ms.
        char: The character currently being typed.
        prev_char: The previously typed character.
        jitter_pct: Percentage of random timing variation (+/- jitter_pct).
        enable_humanize: Whether humanization features (jitter & pauses) are active.

    Returns:
        Delay in milliseconds (float).
    """
    if base_delay_ms <= 0:
        return 0.0

    if not enable_humanize:
        return float(base_delay_ms)

    # 1. Base jitter variation (+/- jitter_pct)
    variation_factor = 1.0 + (random.uniform(-jitter_pct, jitter_pct) / 100.0)
    delay = max(0.5, base_delay_ms * variation_factor)

    # 2. Natural human pauses on structural syntax boundaries
    if char == "\n":
        # Newline pause (human thought break after completing a statement/line)
        delay += random.uniform(40.0, 100.0)
    elif char in ("{", "}", ";", ":"):
        # Block delimiter / statement end pause
        delay += random.uniform(15.0, 35.0)
    elif char == " " and prev_char not in (" ", "\t", "\n"):
        # Space between words pause
        delay += random.uniform(8.0, 20.0)

    return max(0.5, delay)


def estimate_typing_duration(
    text: str,
    base_delay_ms: float,
    enable_humanize: bool = False,
    typo_rate_pct: float = 0.0,
) -> Tuple[float, int]:
    """
    Calculate estimated duration and effective Words Per Minute (WPM)
    for transmitting the given text.

    Args:
        text: The target text to type.
        base_delay_ms: Keystroke delay in ms.
        enable_humanize: Whether humanized timing is enabled.
        typo_rate_pct: Simulated typo frequency percentage (0-5%).

    Returns:
        Tuple of (estimated_duration_seconds, estimated_wpm).
    """
    if not text or base_delay_ms <= 0:
        return 0.0, 0

    total_ms = 0.0
    prev_char = ""
    for char in text:
        # Use average variation (jitter average is 0, add mean boundary pauses)
        if enable_humanize:
            char_delay = base_delay_ms
            if char == "\n":
                char_delay += 70.0
            elif char in ("{", "}", ";", ":"):
                char_delay += 25.0
            elif char == " " and prev_char not in (" ", "\t", "\n"):
                char_delay += 14.0
            total_ms += char_delay

            # Typo adds mistake stroke + human notice reaction (~120ms) + backspace stroke + correct stroke
            if typo_rate_pct > 0.0 and char.isalnum() and random.uniform(0.0, 100.0) < typo_rate_pct:
                total_ms += base_delay_ms + 120.0 + 15.0
        else:
            total_ms += base_delay_ms
        prev_char = char

    total_seconds = total_ms / 1000.0
    minutes = total_seconds / 60.0

    total_chars = len(text)
    # Standard WPM calculation: 5 characters per word
    words = total_chars / 5.0
    wpm = int(words / minutes) if minutes > 0 else 0

    return total_seconds, wpm

