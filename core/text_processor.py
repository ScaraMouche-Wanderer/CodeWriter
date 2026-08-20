"""
Text processing transformations for CodeTyper.
Pure functions with no external dependencies (zero UI/subprocess/backend imports).
"""

import re


def preserve(text: str) -> str:
    """
    Identity transform. Returns text unchanged.
    Exists for symmetry with smart() so callers can treat both modes uniformly
    (e.g., dict lookup {"preserve": preserve, "smart": smart}).
    """
    return text


def smart(text: str) -> str:
    """
    Removes leading and trailing whitespace from EACH line independently while
    preserving blank lines as empty lines.

    Rules:
    - Split on '\n', strip leading and trailing whitespace from each line.
    - Preserve blank lines as empty lines (not removed or collapsed).
    - Rejoin lines with '\n'.
    - Empty string returns empty string.
    """
    if not text:
        return ""

    lines = text.split("\n")
    processed_lines = [line.strip() for line in lines]
    return "\n".join(processed_lines)


# ── Line number patterns ──────────────────────────────────────
# Matches common line number prefixes from various sources:
#   "  1: code"    "1. code"    " 42 | code"    "123| code"    "  7  code" (leading digits + spaces)
_LINE_NUM_COLON = re.compile(r"^\s*\d+\s*:\s?")       # "  1: " or "123: "
_LINE_NUM_DOT = re.compile(r"^\s*\d+\.\s")            # "1. "
_LINE_NUM_PIPE = re.compile(r"^\s*\d+\s*\|\s?")       # " 42 | " or "7| "


def _detect_line_number_pattern(text: str) -> re.Pattern | None:
    """
    Inspects the first few non-empty lines to detect a consistent
    line-number prefix pattern. Returns the matching regex, or None
    if no pattern is detected.

    We require at least 2 out of the first 5 non-empty lines to match
    the same pattern to avoid false-positive stripping of lines that
    just happen to start with a digit.
    """
    non_empty = [line for line in text.split("\n") if line.strip()][:5]
    if len(non_empty) < 1:
        return None

    for pattern in (_LINE_NUM_COLON, _LINE_NUM_DOT, _LINE_NUM_PIPE):
        matches = sum(1 for line in non_empty if pattern.match(line))
        threshold = 2 if len(non_empty) >= 2 else 1
        if matches >= threshold:
            return pattern

    return None


def strip_line_numbers(text: str) -> str:
    """
    Detects and strips leading line-number prefixes from each line.

    Supported formats:
    - "  1: code"     → "code"        (colon-separated, e.g., view_file output)
    - "1. code"       → "code"        (dot-separated, e.g., numbered lists)
    - " 42 | code"    → "code"        (pipe-separated, e.g., some IDEs)

    Detection requires at least 2 of the first 5 non-empty lines to match
    a consistent pattern. If no pattern is detected, returns text unchanged
    (falls through to preserve behavior).
    """
    if not text:
        return ""

    pattern = _detect_line_number_pattern(text)
    if pattern is None:
        return text

    lines = text.split("\n")
    stripped = [pattern.sub("", line) for line in lines]
    return "\n".join(stripped)


def compensate_auto_close(text: str) -> str:
    """
    Compensates for web IDEs that automatically insert closing pairs ((), [], {}, "", '').
    Suppresses redundant immediately-adjacent closing pairs (e.g. () -> (, [] -> [, {} -> {)
    that cause duplicate brackets in auto-closing editors.
    """
    if not text:
        return ""

    # Replace immediately closed empty pairs where the IDE auto-inserts the closer
    res = text.replace("()", "(").replace("[]", "[").replace("{}", "{")
    return res

