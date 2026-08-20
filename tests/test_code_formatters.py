"""
Unit tests for code formatters, beautifiers, and encoders in core.code_tools.
"""

from core.code_tools import (
    decode_base64,
    decode_url,
    encode_base64,
    encode_url,
    format_html,
    format_json,
    format_sql,
    minify_json,
)


def test_format_json_valid() -> None:
    """Valid JSON string is formatted with indentation."""
    raw = '{"name":"CodeWriter","features":["typing","stealth"],"count":42}'
    ok, formatted = format_json(raw, indent=2)
    assert ok is True
    assert '"name": "CodeWriter"' in formatted
    assert "  " in formatted


def test_format_json_invalid() -> None:
    """Invalid JSON returns error without throwing."""
    raw = '{"name": "broken'
    ok, err = format_json(raw)
    assert ok is False
    assert "Invalid JSON" in err


def test_minify_json() -> None:
    """JSON is compacted into a single line without spaces."""
    raw = """
    {
      "key": "value",
      "nums": [1, 2, 3]
    }
    """
    ok, minified = minify_json(raw)
    assert ok is True
    assert minified == '{"key":"value","nums":[1,2,3]}'


def test_format_sql() -> None:
    """SQL keywords are capitalized and major clauses line-broken."""
    raw = "select id, name, email from users where active = 1 order by id desc limit 10;"
    formatted = format_sql(raw)
    assert "SELECT" in formatted
    assert "FROM users" in formatted
    assert "WHERE" in formatted
    assert "ORDER BY" in formatted
    assert "LIMIT 10" in formatted


def test_format_html() -> None:
    """HTML elements are nested and indented properly."""
    raw = "<div><p>Hello <span>World</span></p><br><input type='text'></div>"
    formatted = format_html(raw, indent_spaces=2)
    lines = formatted.splitlines()
    assert lines[0] == "<div>"
    assert lines[-1] == "</div>"
    assert any("  <p>" in l for l in lines)


def test_base64_encode_decode() -> None:
    """Base64 encoding and decoding round-trip cleanly."""
    original = "CodeWriter — Professional Linux Keystroke Engine 🚀"
    encoded = encode_base64(original)
    assert isinstance(encoded, str)
    assert len(encoded) > 0

    ok, decoded = decode_base64(encoded)
    assert ok is True
    assert decoded == original


def test_base64_decode_invalid() -> None:
    """Invalid Base64 returns error gracefully."""
    ok, msg = decode_base64("!@#$%^&*")
    assert ok is False
    assert "Invalid Base64" in msg


def test_url_encode_decode() -> None:
    """URL percent encoding and decoding work seamlessly."""
    original = "https://example.com/api?query=hello world & code=c++"
    encoded = encode_url(original)
    assert "hello%20world" in encoded
    assert "c%2B%2B" in encoded

    decoded = decode_url(encoded)
    assert decoded == original
