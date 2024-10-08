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

    def compile(self, query: _Query, offset: int = 0) -> JSONPathQuery:  # noqa: A003
        return JSONPathQuery(
            env=self,
            segments=tuple(self._parse_segment(s, offset) for s in query.segments),
        )

    def from_symbol(self, s: str, span: tuple[int, int]) -> JSONPathQuery:
        return JSONPathQuery(
            env=self,
            segments=(
                JSONPathChildSegment(
                    env=self,
                    span=span,
                    selectors=(NameSelector(env=self, span=span, name=s),),
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

    # TODO: change span to token!

    def _parse_segment(self, segment: _Segment, offset: int) -> JSONPathSegment:
        match segment:
            case _Segment.Child(selectors, span):
                return JSONPathChildSegment(
                    env=self,
                    span=(span[0] + offset, span[1] + offset),
                    selectors=tuple(self._parse_selector(s, offset) for s in selectors),
                )
            case _Segment.Recursive(selectors, span):
                return JSONPathRecursiveDescentSegment(
                    env=self,
                    span=(span[0] + offset, span[1] + offset),
                    selectors=tuple(self._parse_selector(s, offset) for s in selectors),
                )
            case _:
                raise Exception(":(")

    def _parse_selector(self, selector: _Selector, offset: int) -> JSONPathSelector:
        match selector:
            case _Selector.Name(name, span):
                return NameSelector(
                    env=self, span=(span[0] + offset, span[1] + offset), name=name
                )
            case _Selector.Index(index, span):
                return IndexSelector(
                    env=self, span=(span[0] + offset, span[1] + offset), index=index
                )
            case _Selector.Slice(start, stop, step, span):
                return SliceSelector(
                    env=self,
                    span=(span[0] + offset, span[1] + offset),
                    start=start,
                    stop=stop,
                    step=step,
                )
            case _Selector.Wild(span):
                return WildcardSelector(
                    env=self, span=(span[0] + offset, span[1] + offset)
                )
            case _Selector.Filter(expression, span):
                return Filter(
                    env=self,
                    span=(span[0] + offset, span[1] + offset),
                    expression=FilterExpression(
                        span=(span[0] + offset, span[1] + offset),
                        expression=self._parse_filter_expression(expression, offset),
                    ),
                )
            case _Selector.SingularQuery(query, span):
                return SingularQuerySelector(
                    env=self,
                    span=(span[0] + offset, span[1] + offset),
                    query=self.compile(query, offset),
                )
            case _:
                raise NotImplementedError(selector.__class__.__name__)

    def _parse_filter_expression(  # noqa: PLR0912
        self, expression: _FilterExpression, offset: int
    ) -> Expression:
        expr: Expression
        match expression:
            case _FilterExpression.True_(span):
                expr = BooleanLiteral(
                    span=(span[0] + offset, span[1] + offset), value=True
                )
            case _FilterExpression.False_(span):
                expr = BooleanLiteral(
                    span=(span[0] + offset, span[1] + offset), value=False
                )
            case _FilterExpression.Null(span):
                expr = NullLiteral(
                    span=(span[0] + offset, span[1] + offset), value=None
                )
            case _FilterExpression.StringLiteral(value, span):
                expr = StringLiteral(
                    span=(span[0] + offset, span[1] + offset), value=value
                )
            case _FilterExpression.Int(value, span):
                expr = IntegerLiteral(
                    span=(span[0] + offset, span[1] + offset), value=value
                )
            case _FilterExpression.Float(value, span):
                expr = FloatLiteral(
                    span=(span[0] + offset, span[1] + offset), value=value
                )
            case _FilterExpression.Not(_expr, span):
                expr = PrefixExpression(
                    span=(span[0] + offset, span[1] + offset),
                    operator="!",
                    right=self._parse_filter_expression(_expr, offset),
                )
            case _FilterExpression.Logical(left, operator, right, span):
                expr = LogicalExpression(
                    span=(span[0] + offset, span[1] + offset),
                    left=self._parse_filter_expression(left, offset),
                    operator=str(operator),
                    right=self._parse_filter_expression(right, offset),
                )
            case _FilterExpression.Comparison(left, operator, right, span):
                expr = ComparisonExpression(
                    span=(span[0] + offset, span[1] + offset),
                    left=self._parse_filter_expression(left, offset),
                    operator=str(operator),
                    right=self._parse_filter_expression(right, offset),
                )
            case _FilterExpression.RelativeQuery(query, span):
                expr = RelativeFilterQuery(
                    span=(span[0] + offset, span[1] + offset),
                    query=self.compile(query, offset),
                )
            case _FilterExpression.RootQuery(query, span):
                expr = RootFilterQuery(
                    span=(span[0] + offset, span[1] + offset),
                    query=self.compile(query, offset),
                )
            case _FilterExpression.Function(name, args, span):
                expr = FunctionExtension(
                    span=(span[0] + offset, span[1] + offset),
                    name=name,
                    args=[self._parse_filter_expression(arg, offset) for arg in args],
                )
            case _:
                # TODO
                raise NotImplementedError

        return expr
