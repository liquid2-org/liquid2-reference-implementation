"""Test the Rust parser."""

import operator
from dataclasses import dataclass

import pytest
from liquid2 import parse


@dataclass
class Case:
    """Test case helper."""

    name: str
    source: str
    want: str


TEST_CASES = [
    Case(
        name="empty template",
        source="",
        want="",
    ),
    Case(
        name="just whitespace",
        source=" \n ",
        want=" \n ",
    ),
    Case(
        name="hello liquid",
        source="Hello, {{ you }}!",
        want="Hello, {{ $['you'] }}!",
    ),
    Case(
        name="basic if tag",
        source="{% if foo %}bar{% endif %}",
        want="{% if $['foo'] %}bar{% endif %}",
    ),
    Case(
        name="basic elsif tag",
        source="{% if foo %}a{% elsif bar %}b{% endif %}",
        want="{% if $['foo'] %}a{% elsif $['bar'] %}b{% endif %}",
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("name"))
def test_parser(case: Case) -> None:
    """Test the Rust parser."""
    assert str(parse(case.source)) == case.want
