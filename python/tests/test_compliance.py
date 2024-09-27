"""Test against the Liquid2 compliance test suite."""

import json
import operator
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import pytest
from liquid2 import Environment

env = Environment()


@dataclass
class Case:
    """Test helper class."""

    name: str
    template: str
    data: dict[str, Any] = field(default_factory=dict)
    result: str | None = None
    invalid: bool | None = None
    tags: list[str] = field(default_factory=list)


# TODO:
FILENAME = "python/tests/liquid2-compliance-test-suite/tests/tags/assign.json"


def cases() -> list[Case]:
    """Read test cases."""
    with open(FILENAME, encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> list[Case]:
    """Return all valid test cases."""
    return [case for case in cases() if not case.invalid]


def invalid_cases() -> list[Case]:
    """Return all invalid test cases."""
    return [case for case in cases() if case.invalid]


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(case: Case) -> None:
    """Test valid templates."""
    assert env.from_string(case.template).render(**case.data) == case.result
