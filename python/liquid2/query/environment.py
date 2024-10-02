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

    def from_symbol(self, s: str, line_col: tuple[int, int]) -> JSONPathQuery:
        return JSONPathQuery(
            env=self,
            segments=(
                JSONPathChildSegment(
                    env=self,
                    line_col=line_col,
                    selectors=(NameSelector(env=self, line_col=line_col, name=s),),
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
            case _Segment.Child(selectors, line_col):
                return JSONPathChildSegment(
                    env=self,
                    line_col=line_col,
                    selectors=tuple(self._parse_selector(s) for s in selectors),
                )
            case _Segment.Recursive(selectors, line_col):
                return JSONPathRecursiveDescentSegment(
                    env=self,
                    line_col=line_col,
                    selectors=tuple(self._parse_selector(s) for s in selectors),
                )
            case _:
                raise Exception(":(")

    def _parse_selector(self, selector: _Selector) -> JSONPathSelector:
        match selector:
            case _Selector.Name(name, line_col):
                return NameSelector(env=self, line_col=line_col, name=name)
            case _Selector.Index(index, line_col):
                return IndexSelector(env=self, line_col=line_col, index=index)
            case _Selector.Slice(start, stop, step, line_col):
                return SliceSelector(
                    env=self, line_col=line_col, start=start, stop=stop, step=step
                )
            case _Selector.Wild(line_col):
                return WildcardSelector(env=self, line_col=line_col)
            case _Selector.Filter(expression, line_col):
                return Filter(
                    env=self,
                    line_col=line_col,
                    expression=FilterExpression(
                        line_col=line_col,
                        expression=self._parse_filter_expression(expression),
                    ),
                )
            case _Selector.SingularQuery(query, line_col):
                return SingularQuerySelector(
                    env=self, line_col=line_col, query=self.compile(query)
                )
            case _:
                raise NotImplementedError(selector.__class__.__name__)

    def _parse_filter_expression(  # noqa: PLR0912
        self, expression: _FilterExpression
    ) -> Expression:
        expr: Expression
        match expression:
            case _FilterExpression.True_(line_col):
                expr = BooleanLiteral(line_col=line_col, value=True)
            case _FilterExpression.False_(line_col):
                expr = BooleanLiteral(line_col=line_col, value=False)
            case _FilterExpression.Null(line_col):
                expr = NullLiteral(line_col=line_col, value=None)
            case _FilterExpression.StringLiteral(value, line_col):
                expr = StringLiteral(line_col=line_col, value=value)
            case _FilterExpression.Int(value, line_col):
                expr = IntegerLiteral(line_col=line_col, value=value)
            case _FilterExpression.Float(value, line_col):
                expr = FloatLiteral(line_col=line_col, value=value)
            case _FilterExpression.Not(_expr, line_col):
                expr = PrefixExpression(
                    line_col=line_col,
                    operator="!",
                    right=self._parse_filter_expression(_expr),
                )
            case _FilterExpression.Logical(left, operator, right, line_col):
                expr = LogicalExpression(
                    line_col=line_col,
                    left=self._parse_filter_expression(left),
                    operator=str(operator),
                    right=self._parse_filter_expression(right),
                )
            case _FilterExpression.Comparison(left, operator, right, line_col):
                expr = ComparisonExpression(
                    line_col=line_col,
                    left=self._parse_filter_expression(left),
                    operator=str(operator),
                    right=self._parse_filter_expression(right),
                )
            case _FilterExpression.RelativeQuery(query, line_col):
                expr = RelativeFilterQuery(line_col=line_col, query=self.compile(query))
            case _FilterExpression.RootQuery(query, line_col):
                expr = RootFilterQuery(line_col=line_col, query=self.compile(query))
            case _FilterExpression.Function(name, args, line_col):
                expr = FunctionExtension(
                    line_col=line_col,
                    name=name,
                    args=[self._parse_filter_expression(arg) for arg in args],
                )
            case _:
                # TODO
                raise NotImplementedError

        return expr
