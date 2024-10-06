from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
from liquid2 import Environment

if TYPE_CHECKING:
    from liquid2 import Template
    from liquid2.query import Query
    from liquid2.static_analysis import Span
    from liquid2.static_analysis import TemplateAnalysis


@pytest.fixture
def env() -> Environment:
    return Environment()


def _assert(
    template: Template,
    *,
    template_refs: dict[Query, list[Span]],
    template_locals: dict[Query, list[Span]],
    template_globals: dict[Query, list[Span]],
    failed_visits: dict[str, list[Span]] | None = None,
    unloadable: dict[str, list[Span]] | None = None,
    raise_for_failures: bool = True,
    template_filters: dict[str, list[Span]] | None = None,
    template_tags: dict[str, list[Span]] | None = None,
) -> None:
    """Assertion helper function."""

    async def coro() -> TemplateAnalysis:
        return await template.analyze_async(raise_for_failures=raise_for_failures)

    def _assert_refs(refs: TemplateAnalysis) -> None:
        assert refs.local_variables == template_locals
        assert refs.global_variables == template_globals
        assert refs.variables, template_refs

        if failed_visits:
            assert refs.failed_visits == failed_visits
        else:
            assert refs.failed_visits == {}

        if unloadable:
            assert refs.unloadable_partials == unloadable
        else:
            assert refs.unloadable_partials == {}

        if template_filters:
            assert refs.filters == template_filters
        else:
            assert refs.filters == {}

        if template_tags:
            assert refs.tags == template_tags
        else:
            assert refs.tags == {}

    _assert_refs(template.analyze(raise_for_failures=raise_for_failures))
    _assert_refs(asyncio.run(coro()))


# def test_analyze_output(env: Environment) -> None:
#     """Test that we can count references in an output statement."""
#     template = env.from_string("{{ x | default: y, allow_false: z }}")

#     expected_template_globals = {
#         "x": [("<string>", 1)],
#         "y": [("<string>", 1)],
#         "z": [("<string>", 1)],
#     }
#     expected_template_locals = {}
#     expected_refs = {
#         "x": [("<string>", 1)],
#         "y": [("<string>", 1)],
#         "z": [("<string>", 1)],
#     }

#     expected_filters = {
#         "default": [("<string>", 1)],
#     }

#     _assert(
#         template,
#         template_refs=expected_refs,
#         template_locals=expected_template_locals,
#         template_globals=expected_template_globals,
#         template_filters=expected_filters,
#     )
