"""
Code transformation and text utility functions for CodeTyper.
Includes AI markdown code extraction, indentation conversion, case transformations,
and line manipulation utilities.
"""

import re
from typing import List


def extract_markdown_code(text: str) -> str:
    """
    Extract pure code block contents from markdown text.
    Useful when copying snippets from AI assistants (ChatGPT, Claude, Gemini, etc.)
    that contain ```language ... ``` fences and conversational prose.

    If multiple code blocks exist, extracts the largest code block.
    If no code fences are found, returns the stripped original text.
    """
    if not text:
        return ""

    # Match ```optional_lang\n ... \n```
    pattern = re.compile(r"```(?:[a-zA-Z0-9_-]+)?\r?\n(.*?)\r?\n```", re.DOTALL)
    matches = pattern.findall(text)

    if matches:
        # Return the longest code block
        return max(matches, key=len).strip()

    # Match unclosed ``` at the start or middle
    single_fence_pattern = re.compile(r"```(?:[a-zA-Z0-9_-]+)?\r?\n(.*)", re.DOTALL)
    match_single = single_fence_pattern.search(text)
    if match_single:
        code_part = match_single.group(1)
        # Strip trailing ``` if present
        if code_part.endswith("```"):
            code_part = code_part[:-3]
        return code_part.strip()

    return text.strip()


def convert_tabs_to_spaces(text: str, space_count: int = 4) -> str:
    """Convert tab characters to a specified number of spaces."""
    spaces = " " * space_count
    return text.replace("\t", spaces)


def convert_spaces_to_tabs(text: str, space_count: int = 4) -> str:
    """Convert leading blocks of spaces to tabs."""
    spaces = " " * space_count
    lines = []
    for line in text.split("\n"):
        leading_spaces = len(line) - len(line.lstrip(" "))
        if leading_spaces > 0:
            tab_count = leading_spaces // space_count
            remainder = leading_spaces % space_count
            new_line = ("\t" * tab_count) + (" " * remainder) + line.lstrip(" ")
            lines.append(new_line)
        else:
            lines.append(line)
    return "\n".join(lines)


def trim_trailing_whitespace(text: str) -> str:
    """Strip trailing spaces and tabs from each line."""
    return "\n".join(line.rstrip() for line in text.split("\n"))


def remove_blank_lines(text: str) -> str:
    """Remove all completely empty or whitespace-only lines."""
    return "\n".join(line for line in text.split("\n") if line.strip())


def deduplicate_lines(text: str) -> str:
    """Remove duplicate lines while preserving the original order of first occurrence."""
    seen = set()
    unique_lines: List[str] = []
    for line in text.split("\n"):
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
    return "\n".join(unique_lines)


def sort_lines(text: str, reverse: bool = False) -> str:
    """Sort non-empty lines alphabetically."""
    lines = text.split("\n")
    lines.sort(reverse=reverse)
    return "\n".join(lines)


def _split_identifier(name: str) -> List[str]:
    """Split an identifier (snake, camel, kebab) into constituent lowercase words."""
    # Replace separators with spaces
    s = re.sub(r"[-_.]+", " ", name)
    # Insert space before capital letters in camelCase
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return [w.lower() for w in s.split() if w]


def change_case(text: str, target: str) -> str:
    """
    Convert an identifier or text selection to a target naming convention.

    Targets:
        'camel':  camelCase
        'pascal': PascalCase
        'snake':  snake_case
        'kebab':  kebab-case
        'upper':  UPPERCASE
        'lower':  lowercase
    """
    if not text:
        return ""

    if target == "upper":
        return text.upper()
    if target == "lower":
        return text.lower()

    words = _split_identifier(text)
    if not words:
        return text

    if target == "camel":
        return words[0] + "".join(w.capitalize() for w in words[1:])
    elif target == "pascal":
        return "".join(w.capitalize() for w in words)
    elif target == "snake":
        return "_".join(words)
    elif target == "kebab":
        return "-".join(words)

def strip_comments_and_docstrings(text: str, lang_id: str = "plain") -> str:
    """
    Language-aware comment and docstring stripper.
    Removes single-line comments, multi-line block comments, and Python docstrings
    while preserving string literals and indentation.
    """
    if not text:
        return ""

    lang = (lang_id or "plain").lower()

    # Determine comment styles based on language
    has_hash_comments = lang in ("python", "sh", "bash", "zsh", "yaml", "toml", "ruby", "php")
    has_slash_comments = lang in (
        "c",
        "cpp",
        "java",
        "rust",
        "go",
        "javascript",
        "typescript",
        "css",
        "php",
        "kotlin",
        "swift",
        "plain",
    )
    has_dash_comments = lang in ("sql", "lua")
    has_html_comments = lang in ("html", "markdown", "xml")
    is_python = lang == "python"

    out = []
    n = len(text)
    i = 0

    while i < n:
        # Check string literals (Single, Double, Triple quotes)
        # Python triple quotes """ or '''
        if is_python and (text[i : i + 3] == '"""' or text[i : i + 3] == "'''"):
            quote = text[i : i + 3]
            # Check if this triple quote is a standalone docstring (preceded only by whitespace on line)
            # Find start of line
            sol = text.rfind("\n", 0, i)
            line_prefix = text[sol + 1 : i] if sol != -1 else text[:i]
            is_docstring = line_prefix.strip() == ""

            end_pos = text.find(quote, i + 3)
            if end_pos != -1:
                if is_docstring:
                    # Skip the docstring and any trailing newline if line is purely docstring
                    i = end_pos + 3
                    if i < n and text[i] == "\n":
                        i += 1
                    continue
                else:
                    out.append(text[i : end_pos + 3])
                    i = end_pos + 3
                    continue
            else:
                out.append(text[i:])
                break

        # Double quote string
        if text[i] == '"':
            out.append('"')
            i += 1
            while i < n:
                ch = text[i]
                out.append(ch)
                if ch == "\\":  # Escaped character
                    i += 1
                    if i < n:
                        out.append(text[i])
                elif ch == '"':
                    i += 1
                    break
                i += 1
            continue

        # Single quote string
        if text[i] == "'":
            out.append("'")
            i += 1
            while i < n:
                ch = text[i]
                out.append(ch)
                if ch == "\\":
                    i += 1
                    if i < n:
                        out.append(text[i])
                elif ch == "'":
                    i += 1
                    break
                i += 1
            continue

        # HTML Comments <!-- ... -->
        if has_html_comments and text[i : i + 4] == "<!--":
            end_pos = text.find("-->", i + 4)
            if end_pos != -1:
                i = end_pos + 3
                continue
            else:
                break

        # C-style Block comments /* ... */
        if (has_slash_comments or lang in ("sql", "css")) and text[i : i + 2] == "/*":
            end_pos = text.find("*/", i + 2)
            if end_pos != -1:
                i = end_pos + 2
                continue
            else:
                break

        # Single-line // comments
        if has_slash_comments and text[i : i + 2] == "//":
            end_pos = text.find("\n", i + 2)
            if end_pos != -1:
                i = end_pos  # Keep the newline
            else:
                break
            continue

        # Single-line # comments
        if has_hash_comments and text[i] == "#":
            end_pos = text.find("\n", i + 1)
            if end_pos != -1:
                i = end_pos  # Keep the newline
            else:
                break
            continue

        # Single-line -- comments (SQL / Lua)
        if has_dash_comments and text[i : i + 2] == "--":
            end_pos = text.find("\n", i + 2)
            if end_pos != -1:
                i = end_pos
            else:
                break
            continue

        out.append(text[i])
        i += 1

    cleaned = "".join(out)
    # Clean trailing whitespace on lines
    cleaned_lines = [line.rstrip() for line in cleaned.split("\n")]
    # Strip excessive consecutive empty lines (leave at most one empty line between blocks)
    final_lines: List[str] = []
    prev_blank = False
    for line in cleaned_lines:
        is_blank = not line.strip()
        if is_blank:
            if not prev_blank:
                final_lines.append("")
                prev_blank = True
        else:
            final_lines.append(line)
            prev_blank = False

    return "\n".join(final_lines).strip()


# ═══════════════════════════════════════════════════════
#  FORMATTERS & BEAUTIFIERS
# ═══════════════════════════════════════════════════════

def format_json(text: str, indent: int = 2) -> Tuple[bool, str]:
    """
    Format JSON string with specified indentation.
    Returns (True, formatted_json) on success, or (False, error_message) on failure.
    """
    if not text or not text.strip():
        return False, "Input is empty"
    try:
        import json
        parsed = json.loads(text)
        return True, json.dumps(parsed, indent=indent, ensure_ascii=False)
    except Exception as e:
        return False, f"Invalid JSON: {e}"


def minify_json(text: str) -> Tuple[bool, str]:
    """
    Minify JSON into a single compact line.
    Returns (True, minified_json) on success, or (False, error_message) on failure.
    """
    if not text or not text.strip():
        return False, "Input is empty"
    try:
        import json
        parsed = json.loads(text)
        return True, json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
    except Exception as e:
        return False, f"Invalid JSON: {e}"


def format_sql(text: str) -> str:
    """
    Format SQL queries with capitalized keywords and indented clauses.
    """
    if not text or not text.strip():
        return ""

    keywords = [
        "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
        "OFFSET", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "CROSS JOIN",
        "JOIN", "ON", "AND", "OR", "NOT", "INSERT INTO", "VALUES", "UPDATE", "SET",
        "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DROP TABLE", "UNION ALL", "UNION",
        "EXISTS", "IN", "BETWEEN", "LIKE", "IS NULL", "IS NOT NULL", "CASE", "WHEN",
        "THEN", "ELSE", "END", "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX"
    ]

    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", text.strip())

    # Case-insensitive keyword replacement with uppercase
    pattern = re.compile(r"\b(" + "|".join(re.escape(kw) for kw in keywords) + r")\b", re.IGNORECASE)
    formatted = pattern.sub(lambda m: m.group(1).upper(), cleaned)

    # Line break major clauses
    major_clauses = [
        "SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
        "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN", "JOIN",
        "INSERT INTO", "VALUES", "UPDATE", "SET", "DELETE FROM", "UNION", "UNION ALL"
    ]
    for clause in major_clauses:
        clause_pattern = re.compile(rf"(?<!^)\b({re.escape(clause)})\b", re.IGNORECASE)
        formatted = clause_pattern.sub(r"\n\1", formatted)

    # Indent lines after SELECT / WHERE / SET
    lines = formatted.split("\n")
    indented_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        first_word = stripped.split()[0].upper()
        if first_word in ("SELECT", "FROM", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "INSERT", "UPDATE", "DELETE", "UNION"):
            indented_lines.append(stripped)
        else:
            indented_lines.append("  " + stripped)

    return "\n".join(indented_lines)


def format_html(text: str, indent_spaces: int = 2) -> str:
    """
    Format HTML/XML tags with clean line indentation.
    """
    if not text or not text.strip():
        return ""

    indent_str = " " * indent_spaces
    tokens = re.findall(r"(<[^>]+>|[^<]+)", text.strip())
    lines: List[str] = []
    level = 0
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    for token in tokens:
        trimmed = token.strip()
        if not trimmed:
            continue
        if trimmed.startswith("</"):
            level = max(0, level - 1)
            lines.append((indent_str * level) + trimmed)
        elif trimmed.startswith("<") and not trimmed.startswith("<!") and not trimmed.startswith("<?"):
            lines.append((indent_str * level) + trimmed)
            tag_match = re.match(r"<([a-zA-Z0-9_-]+)", trimmed)
            tag_name = tag_match.group(1).lower() if tag_match else ""
            is_self_closing = trimmed.endswith("/>") or tag_name in void_tags
            if not is_self_closing:
                level += 1
        elif trimmed.startswith("<!") or trimmed.startswith("<?"):
            lines.append((indent_str * level) + trimmed)
        else:
            lines.append((indent_str * level) + trimmed)

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
#  ENCODERS & DECODERS
# ═══════════════════════════════════════════════════════

def encode_base64(text: str) -> str:
    """Encode string to Base64 (UTF-8)."""
    import base64
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode_base64(text: str) -> Tuple[bool, str]:
    """Decode Base64 string into UTF-8 text."""
    import base64
    try:
        decoded_bytes = base64.b64decode(text.strip().encode("ascii"), validate=True)
        return True, decoded_bytes.decode("utf-8")
    except Exception as e:
        return False, f"Invalid Base64: {e}"


def encode_url(text: str) -> str:
    """Percent-encode a string for URL usage."""
    import urllib.parse
    return urllib.parse.quote(text)


def decode_url(text: str) -> str:
    """Decode percent-encoded URL string."""
    import urllib.parse
    return urllib.parse.unquote(text)

