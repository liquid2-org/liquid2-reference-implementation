"""Auto escape HTML test cases."""

import operator
from typing import Any
from typing import NamedTuple

import pytest
from liquid2 import Environment
from markupsafe import Markup


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


filter_test_cases = [
    Case(
        description="join unsafe iterable and default separator",
        template=r"{{ foo | join }}",
        context={"foo": ["<p>hello</p>", "<p>goodbye</p>"]},
        expect="&lt;p&gt;hello&lt;/p&gt; &lt;p&gt;goodbye&lt;/p&gt;",
    ),
    Case(
        description="join unsafe iterable and unsafe separator",
        template=r"{{ foo | join: bar }}",
        context={"foo": ["<p>hello</p>", "<p>goodbye</p>"], "bar": "<hr>"},
        expect="&lt;p&gt;hello&lt;/p&gt;&lt;hr&gt;&lt;p&gt;goodbye&lt;/p&gt;",
    ),
    Case(
        description="join safe iterable and default separator",
        template=r"{{ foo | join }}",
        context={"foo": [Markup("<p>hello</p>"), Markup("<p>goodbye</p>")]},
        expect="<p>hello</p> <p>goodbye</p>",
    ),
    Case(
        description="join safe iterable and unsafe separator",
        template=r"{{ foo | join: bar }}",
        context={
            "foo": [Markup("<p>hello</p>"), Markup("<p>goodbye</p>")],
            "bar": "<hr>",
        },
        expect="&lt;p&gt;hello&lt;/p&gt;&lt;hr&gt;&lt;p&gt;goodbye&lt;/p&gt;",
    ),
    Case(
        description="join safe iterable and safe separator",
        template=r"{{ foo | join: bar }}",
        context={
            "foo": [Markup("<p>hello</p>"), Markup("<p>goodbye</p>")],
            "bar": Markup("<hr>"),
        },
        expect="<p>hello</p><hr><p>goodbye</p>",
    ),
    Case(
        description="join mixed iterable and safe separator",
        template=r"{{ foo | join: bar }}",
        context={
            "foo": [Markup("<p>hello</p>"), "<p>goodbye</p>"],
            "bar": Markup("<hr>"),
        },
        expect="<p>hello</p><hr>&lt;p&gt;goodbye&lt;/p&gt;",
    ),
    Case(
        description="upcase",
        template=r"{{ name | upcase }}",
        context={"name": '<script>alert("XSS!");</script>'},
        expect="&lt;SCRIPT&gt;ALERT(&#34;XSS!&#34;);&lt;/SCRIPT&gt;",
    ),
    Case(
        description="upcase safe",
        template=r"{{ name | upcase }}",
        context={"name": Markup('<script>alert("XSS!");</script>')},
        expect='<SCRIPT>ALERT("XSS!");</SCRIPT>',
    ),
    Case(
        description="downcase",
        template=r"{{ name | downcase }}",
        context={"name": '<script>alert("XSS!");</script>'},
        expect="&lt;script&gt;alert(&#34;xss!&#34;);&lt;/script&gt;",
    ),
    Case(
        description="downcase safe",
        template=r"{{ name | downcase }}",
        context={"name": Markup('<script>alert("XSS!");</script>')},
        expect='<script>alert("xss!");</script>',
    ),
    Case(
        description="capitalize",
        template=r"{{ name | capitalize }}",
        context={"name": '<script>alert("XSS!");</script>'},
        expect="&lt;script&gt;alert(&#34;xss!&#34;);&lt;/script&gt;",
    ),
    Case(
        description="capitalize safe",
        template=r"{{ name | capitalize }}",
        context={"name": Markup('<script>alert("XSS!");</script>')},
        expect='<script>alert("xss!");</script>',
    ),
    Case(
        description="append unsafe left value and unsafe argument",
        template=r"{{ some | append: other }}",
        context={"some": "<br>", "other": "<hr>"},
        expect="&lt;br&gt;&lt;hr&gt;",
    ),
    Case(
        description="append safe left value and unsafe argument",
        template=r"{{ some | append: other }}",
        context={"some": Markup("<br>"), "other": "<hr>"},
        expect="<br>&lt;hr&gt;",
    ),
    Case(
        description="append safe left value and safe argument",
        template=r"{{ some | append: other }}",
        context={"some": Markup("<br>"), "other": Markup("<hr>")},
        expect="<br><hr>",
    ),
    Case(
        description="lstrip",
        template=r"{{ some | lstrip }}",
        context={"some": "   <br>"},
        expect="&lt;br&gt;",
    ),
    Case(
        description="lstrip safe",
        template=r"{{ some | lstrip }}",
        context={"some": Markup("   <br>")},
        expect="<br>",
    ),
    Case(
        description="newline to BR",
        template=r"{{ some | newline_to_br }}",
        context={"some": "<em>hello</em>\n<b>goodbye</b>"},
        expect="&lt;em&gt;hello&lt;/em&gt;<br />\n&lt;b&gt;goodbye&lt;/b&gt;",
    ),
    Case(
        description="newline to BR safe",
        template=r"{{ some | newline_to_br }}",
        context={"some": Markup("<em>hello</em>\n<b>goodbye</b>")},
        expect="<em>hello</em><br />\n<b>goodbye</b>",
    ),
    Case(
        description="newline to BR chained filter",
        template=r"{{ some | newline_to_br | upcase }}",
        context={"some": "<em>hello</em>\n<b>goodbye</b>"},
        expect="&LT;EM&GT;HELLO&LT;/EM&GT;<BR />\n&LT;B&GT;GOODBYE&LT;/B&GT;",
    ),
    Case(
        description="newline to BR safe chained filter",
        template=r"{{ some | newline_to_br | upcase }}",
        context={"some": Markup("<em>hello</em>\n<b>goodbye</b>")},
        expect="<EM>HELLO</EM><BR />\n<B>GOODBYE</B>",
    ),
    Case(
        description="prepend unsafe left value and unsafe argument",
        template=r"{{ some | prepend: other }}",
        context={"some": "<br>", "other": "<hr>"},
        expect="&lt;hr&gt;&lt;br&gt;",
    ),
    Case(
        description="prepend safe left value and unsafe argument",
        template=r"{{ some | prepend: other }}",
        context={"some": Markup("<br>"), "other": "<hr>"},
        expect="&lt;hr&gt;<br>",
    ),
    Case(
        description="prepend safe left value and safe argument",
        template=r"{{ some | prepend: other }}",
        context={"some": Markup("<br>"), "other": Markup("<hr>")},
        expect="<hr><br>",
    ),
    Case(
        description="remove unsafe left value and unsafe argument",
        template=r"{{ some | remove: other }}",
        context={"some": "<br><p>hello</p><br>", "other": "<br>"},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="remove safe left value and unsafe argument",
        template=r"{{ some | remove: other }}",
        context={"some": Markup("<br><p>hello</p><br>"), "other": "<br>"},
        expect="<br><p>hello</p><br>",
    ),
    Case(
        description="remove safe left value and safe argument",
        template=r"{{ some | remove: other }}",
        context={
            "some": Markup("<br><p>hello</p><br>"),
            "other": Markup("<br>"),
        },
        expect="<p>hello</p>",
    ),
    Case(
        description="remove first unsafe left value and unsafe argument",
        template=r"{{ some | remove_first: other }}",
        context={"some": "<br><p>hello</p><br>", "other": "<br>"},
        expect="&lt;p&gt;hello&lt;/p&gt;&lt;br&gt;",
    ),
    Case(
        description="remove first safe left value and unsafe argument",
        template=r"{{ some | remove_first: other }}",
        context={"some": Markup("<br><p>hello</p><br>"), "other": "<br>"},
        expect="<br><p>hello</p><br>",
    ),
    Case(
        description="remove first safe left value and safe argument",
        template=r"{{ some | remove_first: other }}",
        context={
            "some": Markup("<br><p>hello</p><br>"),
            "other": Markup("<br>"),
        },
        expect="<p>hello</p><br>",
    ),
    Case(
        description="replace unsafe left value and unsafe arguments",
        template=r"{{ some | replace: seq, sub }}",
        context={
            "some": "<br><p>hello</p><br>",
            "seq": "<br>",
            "sub": "<hr>",
        },
        expect="&lt;hr&gt;&lt;p&gt;hello&lt;/p&gt;&lt;hr&gt;",
    ),
    Case(
        description="replace safe left value and unsafe arguments",
        template=r"{{ some | replace: seq, sub }}",
        context={
            "some": Markup("<br><p>hello</p><br>"),
            "seq": "<br>",
            "sub": "<hr>",
        },
        expect="<br><p>hello</p><br>",
    ),
    Case(
        description="replace safe left value and safe arguments",
        template=r"{{ some | replace: seq, sub }}",
        context={
            "some": Markup("<br><p>hello</p><br>"),
            "seq": Markup("<br>"),
            "sub": Markup("<hr>"),
        },
        expect="<hr><p>hello</p><hr>",
    ),
    Case(
        description="replace first - unsafe left value and unsafe arguments",
        template=r"{{ some | replace_first: seq, sub }}",
        context={
            "some": "<br><p>hello</p><br>",
            "seq": "<br>",
            "sub": "<hr>",
        },
        expect="&lt;hr&gt;&lt;p&gt;hello&lt;/p&gt;&lt;br&gt;",
    ),
    Case(
        description="replace first - safe left value and unsafe arguments",
        template=r"{{ some | replace_first: seq, sub }}",
        context={
            "some": Markup("<br><p>hello</p><br>"),
            "seq": "<br>",
            "sub": "<hr>",
        },
        expect="<br><p>hello</p><br>",
    ),
    Case(
        description="replace first - safe left value and safe arguments",
        template=r"{{ some | replace_first: seq, sub }}",
        context={
            "some": Markup("<br><p>hello</p><br>"),
            "seq": Markup("<br>"),
            "sub": Markup("<hr>"),
        },
        expect="<hr><p>hello</p><br>",
    ),
    Case(
        description="slice",
        template=r"{{ some | slice: 4, 12 }}",
        context={"some": "<br><p>hello</p><br>"},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="slice safe",
        template=r"{{ some | slice: 4, 12 }}",
        context={"some": Markup("<br><p>hello</p><br>")},
        expect="<p>hello</p>",
    ),
    Case(
        description="split unsafe left value and unsafe argument",
        template=r"{{ some | split: other }}",
        context={"some": "<p>hello</p><br><p>goodbye</p>", "other": "<br>"},
        expect="&lt;p&gt;hello&lt;/p&gt;&lt;p&gt;goodbye&lt;/p&gt;",
    ),
    Case(
        description="split safe left value and unsafe argument",
        template=r"{{ some | split: other }}",
        context={
            "some": Markup("<p>hello</p><br><p>goodbye</p>"),
            "other": "<br>",
        },
        expect="<p>hello</p><p>goodbye</p>",
    ),
    Case(
        description="split safe left value and safe argument",
        template=r"{{ some | split: other }}",
        context={
            "some": Markup("<p>hello</p><br><p>goodbye</p>"),
            "other": Markup("<br>"),
        },
        expect="<p>hello</p><p>goodbye</p>",
    ),
    Case(
        description="strip",
        template=r"{{ some | strip }}",
        context={"some": "\n<p>hello</p>  \n"},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="strip safe",
        template=r"{{ some | strip }}",
        context={"some": Markup("\n<p>hello</p>  \n")},
        expect="<p>hello</p>",
    ),
    Case(
        description="right strip",
        template=r"{{ some | rstrip }}",
        context={"some": "\n<p>hello</p>  \n"},
        expect="\n&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="right strip safe",
        template=r"{{ some | rstrip }}",
        context={"some": Markup("\n<p>hello</p>  \n")},
        expect="\n<p>hello</p>",
    ),
    Case(
        description="strip html",
        template=r"{{ some | strip_html }}",
        context={"some": "<p>hello</p>"},
        expect="hello",
    ),
    Case(
        description="strip html safe",
        template=r"{{ some | strip_html }}",
        context={"some": Markup("<p>hello</p>")},
        expect="hello",
    ),
    Case(
        description="strip newlines",
        template=r"{{ some | strip_newlines }}",
        context={"some": "\n<p>hello</p>  \n"},
        expect="&lt;p&gt;hello&lt;/p&gt;  ",
    ),
    Case(
        description="strip newlines safe",
        template=r"{{ some | strip_newlines }}",
        context={"some": Markup("\n<p>hello</p>  \n")},
        expect="<p>hello</p>  ",
    ),
    Case(
        description="truncate",
        template=r"{{ some | truncate: 10, '' }}",
        context={"some": "<p>hello</p>"},
        expect="&lt;p&gt;hello&lt;/",
    ),
    Case(
        description="truncate safe",
        template=r"{{ some | truncate: 10, '' }}",
        context={"some": Markup("<p>hello</p>")},
        expect="&lt;p&gt;hello&lt;/",
    ),
    Case(
        description="truncate words",
        template=r"{{ some | truncatewords: 3 }}",
        context={"some": "<em>Ground</em> control to Major Tom."},
        expect="&lt;em&gt;Ground&lt;/em&gt; control to...",
    ),
    Case(
        description="truncate words safe",
        template=r"{{ some | truncatewords: 3 }}",
        context={"some": Markup("<em>Ground</em> control to Major Tom.")},
        expect="&lt;em&gt;Ground&lt;/em&gt; control to...",
    ),
    Case(
        description="URL encode",
        template=r"{{ some | url_encode }}",
        context={"some": "<p>hello</p>"},
        expect=r"%3Cp%3Ehello%3C%2Fp%3E",
    ),
    Case(
        description="URL encode safe",
        template=r"{{ some | url_encode }}",
        context={"some": Markup("<p>hello</p>")},
        expect=r"%3Cp%3Ehello%3C%2Fp%3E",
    ),
    Case(
        description="URL decode",
        template=r"{{ some | url_decode }}",
        context={"some": r"%3Cp%3Ehello%3C%2Fp%3E"},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="URL decode safe",
        template=r"{{ some | url_decode }}",
        context={"some": Markup(r"%3Cp%3Ehello%3C%2Fp%3E")},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="liquid escape",
        template=r"{{ some | escape }}",
        context={"some": "<p>hello</p>"},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="liquid escape markup",
        template=r"{{ some | escape }}",
        context={"some": Markup("<p>hello</p>")},
        expect="&lt;p&gt;hello&lt;/p&gt;",
    ),
    Case(
        description="escape once",
        template=r"{{ some | escape_once }}",
        context={"some": "&lt;p&gt;test&lt;/p&gt;<p>test</p>"},
        expect="&lt;p&gt;test&lt;/p&gt;&lt;p&gt;test&lt;/p&gt;",
    ),
    Case(
        description="escape once markup",
        template=r"{{ some | escape_once }}",
        context={"some": Markup("&lt;p&gt;test&lt;/p&gt;<p>test</p>")},
        expect="&lt;p&gt;test&lt;/p&gt;&lt;p&gt;test&lt;/p&gt;",
    ),
    Case(
        description="escape __html__",
        template=r"{{ some | escape }}",
        context={"some": SafeHTMLDrop([1, 2, 3])},
        expect="SafeHTMLDrop",
    ),
    Case(
        description="safe from unsafe",
        template=r"<p>Hello, {{ you | safe }}</p>",
        context={"you": "<em>World!</em>"},
        expect="<p>Hello, <em>World!</em></p>",
    ),
    Case(
        description="safe from safe",
        template=r"<p>Hello, {{ you | safe }}</p>",
        context={"you": Markup("<em>World!</em>")},
        expect="<p>Hello, <em>World!</em></p>",
    ),
]


@pytest.mark.parametrize(
    "case", filter_test_cases, ids=operator.attrgetter("description")
)
def test_filter_auto_escape(case: Case) -> None:
    env = Environment(auto_escape=True)
    assert env.from_string(case.template).render(**case.context) == case.expect
