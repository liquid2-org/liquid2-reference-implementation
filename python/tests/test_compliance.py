"""Test against the Liquid2 compliance test suite."""

import asyncio
import json
import operator
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import pytest
from liquid2 import Environment
from liquid2.exceptions import Error


@dataclass
class Case:
    """Test helper class."""

    name: str
    template: str
    data: dict[str, Any] = field(default_factory=dict)
    result: str | None = None
    invalid: bool | None = None
    tags: list[str] = field(default_factory=list)


FILENAME = "python/tests/liquid2-compliance-test-suite/cts.json"


def cases() -> list[Case]:
    with open(FILENAME, encoding="utf8") as fd:
        data = json.load(fd)
    return [Case(**case) for case in data["tests"]]


def valid_cases() -> list[Case]:
    return [case for case in cases() if not case.invalid]


def invalid_cases() -> list[Case]:
    return [case for case in cases() if case.invalid]


@pytest.fixture
def env() -> Environment:
    return Environment()


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance(env: Environment, case: Case) -> None:
    assert env.from_string(case.template).render(**case.data) == case.result


@pytest.mark.parametrize("case", valid_cases(), ids=operator.attrgetter("name"))
def test_compliance_async(env: Environment, case: Case) -> None:
    template = env.from_string(case.template)

    async def coro() -> str:
        return template.render(**case.data)

    assert asyncio.run(coro()) == case.result


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_compliance(env: Environment, case: Case) -> None:
    with pytest.raises(Error):
        env.from_string(case.template).render(**case.data)


@pytest.mark.parametrize("case", invalid_cases(), ids=operator.attrgetter("name"))
def test_invalid_compliance_async(env: Environment, case: Case) -> None:
    async def coro() -> str:
        template = env.from_string(case.template)
        return template.render(**case.data)

    with pytest.raises(Error):
        asyncio.run(coro())
