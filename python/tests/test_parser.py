import operator
from dataclasses import dataclass
import pytest
from liquid2 import parse


@dataclass
class Case:
    name: str
    source: str
    want: str


TEST_CASES = [
    Case(
        name="hello liquid",
        source="Hello, {{ you }}!",
        want="Hello, {{ $['you'] }}!",
    ),
]


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("name"))
def test_parser(case: Case) -> None:
    assert str(parse(case.source)) == case.want
