"""Unit tests for core.code_tools module."""

from core.code_tools import (
    change_case,
    convert_spaces_to_tabs,
    convert_tabs_to_spaces,
    deduplicate_lines,
    extract_markdown_code,
    remove_blank_lines,
    sort_lines,
    strip_comments_and_docstrings,
    trim_trailing_whitespace,
)



def test_extract_markdown_code_fenced():
    md = """Here is the solution to your problem:

```python
def add(a, b):
    return a + b
```

Hope that helps!"""
    assert extract_markdown_code(md) == "def add(a, b):\n    return a + b"


def test_extract_markdown_code_multiple_fences():
    md = """First snippet:
```python
x = 1
```
Main logic:
```python
def process_data(data):
    for item in data:
        print(item)
    return True
```
"""
    # Should pick the largest block
    res = extract_markdown_code(md)
    assert "def process_data" in res


def test_extract_markdown_code_no_fences():
    plain = "print('hello world')\nx = 10"
    assert extract_markdown_code(plain) == plain


def test_convert_tabs_to_spaces():
    text = "\tdef foo():\n\t\tpass"
    converted = convert_tabs_to_spaces(text, space_count=4)
    assert converted == "    def foo():\n        pass"


def test_convert_spaces_to_tabs():
    text = "    def foo():\n        pass"
    converted = convert_spaces_to_tabs(text, space_count=4)
    assert converted == "\tdef foo():\n\t\tpass"


def test_trim_trailing_whitespace():
    text = "hello   \nworld\t\t\nfoo"
    assert trim_trailing_whitespace(text) == "hello\nworld\nfoo"


def test_remove_blank_lines():
    text = "line1\n\n   \nline2\n\nline3"
    assert remove_blank_lines(text) == "line1\nline2\nline3"


def test_deduplicate_lines():
    text = "apple\nbanana\napple\norange\nbanana\ncherry"
    assert deduplicate_lines(text) == "apple\nbanana\norange\ncherry"


def test_sort_lines():
    text = "banana\napple\ncherry"
    assert sort_lines(text, reverse=False) == "apple\nbanana\ncherry"
    assert sort_lines(text, reverse=True) == "cherry\nbanana\napple"


def test_change_case():
    assert change_case("user_first_name", "camel") == "userFirstName"
    assert change_case("userFirstName", "snake") == "user_first_name"
    assert change_case("userFirstName", "kebab") == "user-first-name"
    assert change_case("user_first_name", "pascal") == "UserFirstName"
    assert change_case("hello_world", "upper") == "HELLO_WORLD"
    assert change_case("HELLO_WORLD", "lower") == "hello_world"


def test_strip_comments_python():
    py_code = '''"""Module docstring."""
# Single line comment
def foo():
    """Function docstring."""
    url = "https://example.com#anchor"  # trailing comment
    return url
'''
    stripped = strip_comments_and_docstrings(py_code, "python")
    assert "Module docstring" not in stripped
    assert "Single line comment" not in stripped
    assert "Function docstring" not in stripped
    assert 'url = "https://example.com#anchor"' in stripped
    assert "return url" in stripped


def test_strip_comments_cpp():
    cpp_code = """// Top header comment
#include <iostream>
/* Multi-line
   block comment */
int main() {
    std::string s = "// not a comment";
    return 0; // exit
}
"""
    stripped = strip_comments_and_docstrings(cpp_code, "cpp")
    assert "Top header comment" not in stripped
    assert "block comment" not in stripped
    assert "exit" not in stripped
    assert 'std::string s = "// not a comment";' in stripped
    assert "return 0;" in stripped


def test_strip_comments_sql():
    sql = """-- Query all users
SELECT * FROM users /* active only */ WHERE status = 'active';
"""
    stripped = strip_comments_and_docstrings(sql, "sql")
    assert "Query all users" not in stripped
    assert "active only" not in stripped
    assert "SELECT * FROM users  WHERE status = 'active';" in stripped

