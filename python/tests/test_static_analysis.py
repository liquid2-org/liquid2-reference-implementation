"""Template static analysis test cases."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from typing import Any
from typing import Iterable
from typing import Mapping
from typing import TypeAlias

import pytest
from liquid2 import Environment
from liquid2.static_analysis import Span

if TYPE_CHECKING:
    from liquid2 import Template
    from liquid2.static_analysis import TemplateAnalysis


@pytest.fixture
def env() -> Environment:  # noqa: D103
    return Environment()


class MockSpan:
    """A mock span containing the location of a variable, tag or filter."""

    __slots__ = ("template_name", "span")

    def __init__(self, start: int, end: int, template_name: str = "<string>") -> None:
        self.template_name = template_name
        self.span = (start, end)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, (Span, MockSpan))
            and self.template_name == other.template_name
            and self.span == other.span
        )

    def __hash__(self) -> int:
        return hash((self.template_name, self.span))

    def __str__(self) -> str:
        return f"{self.template_name}[{self.span[0]}:{self.span[1]}]"


_Span = MockSpan
MockRefs: TypeAlias = Mapping[str, MockSpan | tuple[MockSpan, ...]]


def _assert(
    template: Template,
    *,
    local_refs: MockRefs,
    global_refs: MockRefs,
    failed_visits: MockRefs | None = None,
    unloadable: MockRefs | None = None,
    raise_for_failures: bool = True,
    filters: MockRefs | None = None,
    tags: MockRefs | None = None,
) -> None:
    all_refs = {**global_refs, **local_refs}

    async def coro() -> TemplateAnalysis:
        return await template.analyze_async(raise_for_failures=raise_for_failures)

    def _assert_refs(refs: TemplateAnalysis) -> None:
        assert _as_strings(refs.local_variables) == _as_strings(local_refs)
        assert _as_strings(refs.global_variables) == _as_strings(global_refs)
        assert _as_strings(refs.variables) == _as_strings(all_refs)

        if failed_visits:
            assert _as_strings(refs.failed_visits) == _as_strings(failed_visits)
        else:
            assert len(refs.failed_visits) == 0

        if unloadable:
            assert _as_strings(refs.unloadable_partials) == _as_strings(unloadable)
        else:
            assert len(refs.unloadable_partials) == 0

        if filters:
            assert _as_strings(refs.filters) == _as_strings(filters)
        else:
            assert len(refs.filters) == 0

        if tags:
            assert _as_strings(refs.tags) == _as_strings(tags)
        else:
            assert len(refs.tags) == 0

    _assert_refs(template.analyze(raise_for_failures=raise_for_failures))
    _assert_refs(asyncio.run(coro()))


def _as_strings(
    refs: Mapping[Any, Any],
) -> dict[str, list[str]]:
    _refs: dict[str, list[str]] = {}
    for k, v in refs.items():
        if isinstance(v, Iterable):
            _refs[str(k)] = [str(_v) for _v in v]
        else:
            _refs[str(k)] = [str(v)]
    return _refs


def test_analyze_output(env: Environment) -> None:
    source = r"{{ x | default: y, allow_false: z }}"

    _assert(
        env.from_string(source),
        local_refs={},
        global_refs={
            "x": _Span(3, 4),
            "y": _Span(16, 17),
            "z": _Span(32, 33),
        },
        filters={
            "default": _Span(7, 14),
        },
    )


def test_bracketed_query_notation(env: Environment) -> None:
    source = r"{{ x['y'].title }}"

    _assert(
        env.from_string(source),
        local_refs={},
        global_refs={"x.y.title": _Span(3, 15)},
    )


def test_nested_queries(env: Environment) -> None:
    source = r"{{ x[y.z].title }}"

    _assert(
        env.from_string(source),
        local_refs={},
        global_refs={
            "x[y.z].title": _Span(3, 15),
            "y.z": _Span(5, 9),
        },
    )
