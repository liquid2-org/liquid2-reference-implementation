"""JSONPath configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import Sequence

from liquid2 import Segment as IRSegment
from liquid2 import Selector as IRSelector

from . import function_extensions
from .query import JSONPathQuery
from .segments import JSONPathChildSegment
from .segments import JSONPathRecursiveDescentSegment
from .selectors import Filter
from .selectors import IndexSelector
from .selectors import NameSelector
from .selectors import SliceSelector
from .selectors import WildcardSelector

if TYPE_CHECKING:
    from liquid2 import FilterExpression as IRFilterExpression
    from liquid2 import Query as IRQuery

    from .filter_expressions import FilterExpression
    from .function_extensions import FilterFunction
    from .segments import JSONPathSegment
    from .selectors import JSONPathSelector


JSONValue = Sequence[Any] | Mapping[str, Any] | str | int | float | None | bool
"""JSON-like data, as you would get from `json.load()`."""


class _JSONPathEnvironment:
    """JSONPath configuration.

    ## Class attributes

    Attributes:
        max_int_index (int): The maximum integer allowed when selecting array items by
            index. Defaults to `(2**53) - 1`.
        min_int_index (int): The minimum integer allowed when selecting array items by
            index. Defaults to `-(2**53) + 1`.
        max_recursion_depth (int): The maximum number of dict/objects and/or
            arrays/lists the recursive descent selector can visit before a
            `JSONPathRecursionError` is thrown.
        parser_class (Parser): The parser to use when parsing tokens from the lexer.
        nondeterministic (bool): If `True`, enable nondeterminism when iterating objects
            and visiting nodes with the recursive descent segment. Defaults to `False`.
    """

    max_int_index = (2**53) - 1
    min_int_index = -(2**53) + 1
    max_recursion_depth = 100

    nondeterministic = False

    def __init__(self) -> None:
        self.function_extensions: dict[str, FilterFunction] = {}
        """A list of function extensions available to filters."""

        self.setup_function_extensions()

    def compile(self, query: IRQuery) -> JSONPathQuery:  # noqa: A003
        return JSONPathQuery(
            env=self, segments=tuple(self._parse_segment(s) for s in query.segments)
        )

    def setup_function_extensions(self) -> None:
        """Initialize function extensions."""
        self.function_extensions["length"] = function_extensions.Length()
        self.function_extensions["count"] = function_extensions.Count()
        self.function_extensions["match"] = function_extensions.Match()
        self.function_extensions["search"] = function_extensions.Search()
        self.function_extensions["value"] = function_extensions.Value()

    def _parse_segment(self, segment: IRSegment) -> JSONPathSegment:
        match segment:
            case IRSegment.Child(selectors):
                return JSONPathChildSegment(
                    env=self,
                    span=(0, 0),
                    selectors=tuple(self._parse_selector(s) for s in selectors),
                )
            case IRSegment.Recursive(selectors):
                return JSONPathRecursiveDescentSegment(
                    env=self,
                    span=(0, 0),
                    selectors=tuple(self._parse_selector(s) for s in selectors),
                )
            case _:
                raise Exception(":(")

    def _parse_selector(self, selector: IRSelector) -> JSONPathSelector:
        match selector:
            case IRSelector.Name(name):
                return NameSelector(env=self, span=(0, 0), name=name)
            case IRSelector.Index(index):
                return IndexSelector(env=self, span=(0, 0), index=index)
            case IRSelector.Slice(start, stop, step):
                return SliceSelector(
                    env=self, span=(0, 0), start=start, stop=stop, step=step
                )
            case IRSelector.Wild():
                return WildcardSelector(env=self, span=(0, 0))
            case IRSelector.Filter(expression):
                return Filter(
                    env=self,
                    span=(0, 0),
                    expression=self._parse_filter_expression(expression),
                )
            case _:
                raise Exception(":(")

    def _parse_filter_expression(
        self, expression: IRFilterExpression
    ) -> FilterExpression:
        raise NotImplementedError(":(")
