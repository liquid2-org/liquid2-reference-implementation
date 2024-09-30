"""JSONPath configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Mapping
from typing import Sequence

from _liquid2 import FilterExpression as _FilterExpression
from _liquid2 import Segment as _Segment
from _liquid2 import Selector as _Selector

from . import function_extensions
from .filter_expressions import BooleanLiteral
from .filter_expressions import ComparisonExpression
from .filter_expressions import Expression
from .filter_expressions import FilterExpression
from .filter_expressions import FloatLiteral
from .filter_expressions import FunctionExtension
from .filter_expressions import IntegerLiteral
from .filter_expressions import LogicalExpression
from .filter_expressions import NullLiteral
from .filter_expressions import PrefixExpression
from .filter_expressions import RelativeFilterQuery
from .filter_expressions import RootFilterQuery
from .filter_expressions import StringLiteral
from .query import JSONPathQuery
from .segments import JSONPathChildSegment
from .segments import JSONPathRecursiveDescentSegment
from .selectors import Filter
from .selectors import IndexSelector
from .selectors import NameSelector
from .selectors import SingularQuerySelector
from .selectors import SliceSelector
from .selectors import WildcardSelector

if TYPE_CHECKING:
    from _liquid2 import Query as _Query

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

    def compile(self, query: _Query) -> JSONPathQuery:  # noqa: A003
        return JSONPathQuery(
            env=self, segments=tuple(self._parse_segment(s) for s in query.segments)
        )

    def from_symbol(self, s: str) -> JSONPathQuery:
        return JSONPathQuery(
            env=self,
            segments=(
                JSONPathChildSegment(
                    env=self,
                    span=(0, 0),
                    selectors=(NameSelector(env=self, span=(0, 0), name=s),),
                ),
            ),
        )

    def setup_function_extensions(self) -> None:
        """Initialize function extensions."""
        self.function_extensions["length"] = function_extensions.Length()
        self.function_extensions["count"] = function_extensions.Count()
        self.function_extensions["match"] = function_extensions.Match()
        self.function_extensions["search"] = function_extensions.Search()
        self.function_extensions["value"] = function_extensions.Value()

    def _parse_segment(self, segment: _Segment) -> JSONPathSegment:
        match segment:
            case _Segment.Child(selectors):
                return JSONPathChildSegment(
                    env=self,
                    span=(0, 0),
                    selectors=tuple(self._parse_selector(s) for s in selectors),
                )
            case _Segment.Recursive(selectors):
                return JSONPathRecursiveDescentSegment(
                    env=self,
                    span=(0, 0),
                    selectors=tuple(self._parse_selector(s) for s in selectors),
                )
            case _:
                raise Exception(":(")

    def _parse_selector(self, selector: _Selector) -> JSONPathSelector:
        match selector:
            case _Selector.Name(name):
                return NameSelector(env=self, span=(0, 0), name=name)
            case _Selector.Index(index):
                return IndexSelector(env=self, span=(0, 0), index=index)
            case _Selector.Slice(start, stop, step):
                return SliceSelector(
                    env=self, span=(0, 0), start=start, stop=stop, step=step
                )
            case _Selector.Wild():
                return WildcardSelector(env=self, span=(0, 0))
            case _Selector.Filter(expression):
                return Filter(
                    env=self,
                    span=(0, 0),
                    expression=FilterExpression(
                        span=(0, 0),
                        expression=self._parse_filter_expression(expression),
                    ),
                )
            case _Selector.SingularQuery(query):
                return SingularQuerySelector(
                    env=self, span=(0, 0), query=self.compile(query)
                )
            case _:
                raise NotImplementedError(selector.__class__.__name__)

    def _parse_filter_expression(  # noqa: PLR0912
        self, expression: _FilterExpression
    ) -> Expression:
        expr: Expression
        match expression:
            case _FilterExpression.True_():
                expr = BooleanLiteral(span=(0, 0), value=True)
            case _FilterExpression.False_():
                expr = BooleanLiteral(span=(0, 0), value=False)
            case _FilterExpression.Null():
                expr = NullLiteral(span=(0, 0), value=None)
            case _FilterExpression.StringLiteral(value):
                expr = StringLiteral(span=(0, 0), value=value)
            case _FilterExpression.Int(value):
                expr = IntegerLiteral(span=(0, 0), value=value)
            case _FilterExpression.Float(value):
                expr = FloatLiteral(span=(0, 0), value=value)
            case _FilterExpression.Not(_expr):
                expr = PrefixExpression(
                    span=(0, 0),
                    operator="!",
                    right=self._parse_filter_expression(_expr),
                )
            case _FilterExpression.Logical(left, operator, right):
                expr = LogicalExpression(
                    span=(0, 0),
                    left=self._parse_filter_expression(left),
                    operator=str(operator),
                    right=self._parse_filter_expression(right),
                )
            case _FilterExpression.Comparison(left, operator, right):
                expr = ComparisonExpression(
                    span=(0, 0),
                    left=self._parse_filter_expression(left),
                    operator=str(operator),
                    right=self._parse_filter_expression(right),
                )
            case _FilterExpression.RelativeQuery(query):
                expr = RelativeFilterQuery(span=(0, 0), query=self.compile(query))
            case _FilterExpression.RootQuery(query):
                expr = RootFilterQuery(span=(0, 0), query=self.compile(query))
            case _FilterExpression.Function(name, args):
                expr = FunctionExtension(
                    span=(0, 0),
                    name=name,
                    args=[self._parse_filter_expression(arg) for arg in args],
                )
            case _:
                # TODO
                raise NotImplementedError

        return expr
