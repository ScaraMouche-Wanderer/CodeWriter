"""
Unit tests for core.text_processor transformations (Smart and Preserve modes).
"""

from core.text_processor import compensate_auto_close, preserve, smart



def test_nested_cpp_class() -> None:
    """Test smart mode strips leading indentation from nested C++ code while preserve leaves it intact."""
    cpp_snippet = (
        "class Solution {\n"
        "public:\n"
        "    int solve(int n) {\n"
        "        if (n <= 0) {\n"
        "            return 0;\n"
        "        }\n"
        "        return n * 2;\n"
        "    }\n"
        "};"
    )

    expected_smart = (
        "class Solution {\n"
        "public:\n"
        "int solve(int n) {\n"
        "if (n <= 0) {\n"
        "return 0;\n"
        "}\n"
        "return n * 2;\n"
        "}\n"
        "};"
    )

    # Smart transform: every non-empty line has 0 leading whitespace
    smart_result = smart(cpp_snippet)
    assert smart_result == expected_smart
    for line in smart_result.split("\n"):
        if line:
            assert not line.startswith(" ")
            assert not line.startswith("\t")

    # Preserve transform: completely unchanged
    assert preserve(cpp_snippet) == cpp_snippet


def test_blank_lines_preservation() -> None:
    """Test blank lines survive as empty lines in output and are not collapsed."""
    code_with_blanks = (
        "def compute():\n"
        "    x = 10\n"
        "\n"
        "    y = 20\n"
        "    \n"
        "    return x + y\n"
    )

    expected_smart = (
        "def compute():\n"
        "x = 10\n"
        "\n"
        "y = 20\n"
        "\n"
        "return x + y\n"
    )

    smart_result = smart(code_with_blanks)
    assert smart_result == expected_smart
    lines = smart_result.split("\n")
    assert lines[2] == ""
    assert lines[4] == ""


def test_mixed_tabs_and_spaces() -> None:
    """Test mixed tabs and spaces indentation are stripped correctly."""
    mixed_code = (
        "\t\tdef tabbed():\n"
        "    \treturn True\n"
        "\t    \tx = 1\n"
    )

    expected_smart = (
        "def tabbed():\n"
        "return True\n"
        "x = 1\n"
    )

    smart_result = smart(mixed_code)
    assert smart_result == expected_smart


def test_trailing_whitespace_stripped() -> None:
    """Test trailing spaces and tabs are stripped from each line."""
    code_with_trailing = (
        "int a = 1;   \n"
        "int b = 2;\t\t\n"
        "int c = 3; \t \n"
    )

    expected_smart = (
        "int a = 1;\n"
        "int b = 2;\n"
        "int c = 3;\n"
    )

    assert smart(code_with_trailing) == expected_smart


def test_empty_string_input() -> None:
    """Test empty string input returns empty string for both functions."""
    assert smart("") == ""
    assert preserve("") == ""


def test_single_line_unindented() -> None:
    """Test single line unindented input returns unchanged for both functions."""
    single_line = "print('hello world')"
    assert smart(single_line) == single_line
    assert preserve(single_line) == single_line


def test_multiline_string_literals_and_raw_strings() -> None:
    """
    Test behavior of multi-line strings and raw literals in both Smart and Preserve modes.
    Preserve mode maintains exact internal whitespace/indentation.
    Smart mode strips per-line leading/trailing whitespace for auto-indenting editors.
    """
    python_docstring = (
        'def get_query():\n'
        '    """\n'
        '    SELECT id, name\n'
        '    FROM users\n'
        '    WHERE active = 1\n'
        '    """\n'
        '    return query\n'
    )

    # Preserve mode leaves all internal indentation completely intact
    assert preserve(python_docstring) == python_docstring

    # Smart mode strips each line's leading/trailing whitespace
    expected_smart = (
        'def get_query():\n'
        '"""\n'
        'SELECT id, name\n'
        'FROM users\n'
        'WHERE active = 1\n'
        '"""\n'
        'return query\n'
    )
    assert smart(python_docstring) == expected_smart

    # C++ raw string literal
    cpp_raw = (
        'const char* json = R"(\n'
        '{\n'
        '    "key": "value",\n'
        '    "list": [1, 2, 3]\n'
        '}\n'
        ')";\n'
    )
    assert preserve(cpp_raw) == cpp_raw
    expected_cpp_smart = (
        'const char* json = R"(\n'
        '{\n'
        '"key": "value",\n'
        '"list": [1, 2, 3]\n'
        '}\n'
        ')";\n'
    )
    assert smart(cpp_raw) == expected_cpp_smart


def test_compensate_auto_close():
    """Test auto-closing bracket compensation replaces empty pairs."""
    code = "def foo():\n    arr = []\n    obj = {}\n"
    compensated = compensate_auto_close(code)
    assert compensated == "def foo(:\n    arr = [\n    obj = {\n"
    assert compensate_auto_close("") == ""


