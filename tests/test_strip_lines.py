"""
Tests for the strip_line_numbers text processing mode.
"""

import pytest

from core.text_processor import strip_line_numbers, _detect_line_number_pattern


class TestDetectLineNumberPattern:
    """Tests for the pattern detection heuristic."""

    def test_detects_colon_pattern(self):
        text = "1: def foo():\n2:     return 1\n3: \n4: bar()"
        pattern = _detect_line_number_pattern(text)
        assert pattern is not None

    def test_detects_dot_pattern(self):
        text = "1. first line\n2. second line\n3. third line"
        pattern = _detect_line_number_pattern(text)
        assert pattern is not None

    def test_detects_pipe_pattern(self):
        text = " 1 | code here\n 2 | more code\n 3 | end"
        pattern = _detect_line_number_pattern(text)
        assert pattern is not None

    def test_no_pattern_in_normal_text(self):
        text = "def foo():\n    return 1\n\nbar()"
        pattern = _detect_line_number_pattern(text)
        assert pattern is None

    def test_no_pattern_single_digit_start(self):
        """A single line starting with a digit shouldn't trigger stripping."""
        text = "3 blind mice"
        pattern = _detect_line_number_pattern(text)
        assert pattern is None

    def test_empty_text(self):
        assert _detect_line_number_pattern("") is None

    def test_only_blank_lines(self):
        assert _detect_line_number_pattern("\n\n\n") is None


class TestStripLineNumbers:
    """Tests for the strip_line_numbers function."""

    def test_empty_string(self):
        assert strip_line_numbers("") == ""

    def test_no_line_numbers(self):
        text = "def hello():\n    return 1"
        assert strip_line_numbers(text) == text

    def test_colon_format(self):
        text = "1: def foo():\n2:     return 1\n3: \n4: bar()"
        result = strip_line_numbers(text)
        assert result == "def foo():\n    return 1\n\nbar()"

    def test_colon_with_leading_spaces(self):
        text = "  1: def foo():\n  2:     return 1\n  3: bar()"
        result = strip_line_numbers(text)
        assert result == "def foo():\n    return 1\nbar()"

    def test_dot_format(self):
        text = "1. import os\n2. import sys\n3. print('hello')"
        result = strip_line_numbers(text)
        assert result == "import os\nimport sys\nprint('hello')"

    def test_pipe_format(self):
        text = " 1 | x = 1\n 2 | y = 2\n 3 | print(x + y)"
        result = strip_line_numbers(text)
        assert result == "x = 1\ny = 2\nprint(x + y)"

    def test_pipe_no_space(self):
        text = "1| line one\n2| line two\n3| line three"
        result = strip_line_numbers(text)
        assert result == "line one\nline two\nline three"

    def test_large_line_numbers(self):
        text = "100: first\n101: second\n102: third"
        result = strip_line_numbers(text)
        assert result == "first\nsecond\nthird"

    def test_preserves_blank_lines(self):
        text = "1: code\n2: \n3: more code"
        result = strip_line_numbers(text)
        assert result == "code\n\nmore code"

    def test_mixed_content_no_stripping(self):
        """If the pattern doesn't match enough lines, text passes through."""
        text = "1: has number\nnormal line\nalso normal\nstill normal\nand normal"
        result = strip_line_numbers(text)
        # Only 1 out of 5 non-empty lines match — below threshold
        assert result == text

    def test_preserves_indentation_after_strip(self):
        text = "1:     indented\n2:         more indent\n3: no indent"
        result = strip_line_numbers(text)
        assert result == "    indented\n        more indent\nno indent"
