"""
Text processing transformations for CodeTyper.
Pure functions with no external dependencies (zero UI/subprocess/backend imports).
"""


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
