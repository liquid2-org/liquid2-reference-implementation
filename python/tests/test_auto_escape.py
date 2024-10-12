from typing import Any
from typing import NamedTuple

import pytest
from liquid2 import Environment


class SafeHTMLDrop:
    def __init__(self, items: list[object]):
        self.items = items

    def __str__(self) -> str:
        return "SafeHTMLDrop"

    def __html__(self) -> str:
        items = "\n".join(f"<li>{item}</li>" for item in self.items)
        return f"<ul>\n{items}\n</ul>"


class Case(NamedTuple):
    """Table driven test case helper."""

    description: str
    template: str
    context: dict[str, Any]
    expect: str


def test_disable_auto_escape() -> None:
    env = Environment(auto_escape=False)
    template = env.from_string(r"{{ content }}")
    assert (
        template.render(content='<script>alert("XSS!");</script>')
        == '<script>alert("XSS!");</script>'
    )


def test_ignore_html_when_auto_escape_is_disabled() -> None:
    env = Environment(auto_escape=False)
    template = env.from_string(r"{{ content }}")
    assert template.render(content=SafeHTMLDrop([1, 2, 3])) == "SafeHTMLDrop"


def test_enable_auto_escape() -> None:
    env = Environment(auto_escape=True)
    template = env.from_string(r"{{ content }}")
    assert (
        template.render(content='<script>alert("XSS!");</script>')
        == "&lt;script&gt;alert(&#34;XSS!&#34;);&lt;/script&gt;"
    )


def test_enable_auto_escape_with_literal_markup() -> None:
    env = Environment(auto_escape=True)
    template = env.from_string(r"{% if true %}<br>{{ content }}<br>{% endif %}")
    assert (
        template.render(content='<script>alert("XSS!");</script>')
        == "<br>&lt;script&gt;alert(&#34;XSS!&#34;);&lt;/script&gt;<br>"
    )


def test_capture_auto_escaped_markup() -> None:
    env = Environment(auto_escape=True)
    template = env.from_string(
        r"{% capture snippet %}"
        r'<p class="snippet">'
        r"{{ content }}"
        r"</p>"
        r"{% endcapture %}"
        r"{{ snippet }}"
    )

    assert template.render(content='<script>alert("XSS!");</script>') == (
        '<p class="snippet">&lt;script&gt;alert(&#34;XSS!&#34;);&lt;/script&gt;</p>'
    )


def test_html_safe_drop() -> None:
    env = Environment(auto_escape=True)
    template = env.from_string(r"{{ content }}")
    assert (
        template.render(content=SafeHTMLDrop([1, 2, 3]))
        == "<ul>\n<li>1</li>\n<li>2</li>\n<li>3</li>\n</ul>"
    )
