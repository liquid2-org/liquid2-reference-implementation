from __future__ import annotations

from enum import Enum
from typing import TypeAlias

class Whitespace(Enum):
    Plus = ...
    Minus = ...
    Smart = ...
    Default = ...

class Markup:
    class Content:
        __match_args__ = ("text", "span")
        @property
        def text(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Raw:
        __match_args__ = ("wc", "text", "span")
        @property
        def wc(self) -> tuple[Whitespace, Whitespace, Whitespace, Whitespace]: ...
        @property
        def text(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Comment:
        __match_args__ = ("wc", "hashes", "text", "span")
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def hashes(self) -> str: ...
        @property
        def text(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Output:
        __match_args__ = ("wc", "expression", "span")
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def expression(self) -> list[Token]: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Tag:
        __match_args__ = ("wc", "name", "expression", "span")
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def name(self) -> str: ...
        @property
        def expression(self) -> list[Token]: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Lines:
        __match_args__ = ("wc", "name", "statements", "span")
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def name(self) -> str: ...
        @property
        def statements(self) -> list[Markup.Tag]: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class EOI:
        pass

class Token:
    class True_:  # noqa: N801
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class False_:  # noqa: N801
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class And:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Or:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class In:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Not:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Contains:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Null:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class If:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Else:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class With:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Required:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class As:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class For:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Eq:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Ne:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Ge:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Gt:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Le:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Lt:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Colon:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Pipe:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class DoublePipe:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Comma:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class LeftParen:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class RightParen:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Assign:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Word:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class StringLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class IntegerLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> int: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class FloatLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> float: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class RangeLiteral:
        __match_args__ = ("start", "stop", "span")
        @property
        def start(self) -> RangeArgument: ...
        @property
        def stop(self) -> RangeArgument: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Query:
        __match_args__ = ("path", "span")
        @property
        def path(self) -> Query: ...
        @property
        def span(self) -> tuple[int, int]: ...

class RangeArgument:
    class StringLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class IntegerLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> int: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class FloatLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> float: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Query:
        __match_args__ = ("path", "span")
        @property
        def path(self) -> Query: ...
        @property
        def span(self) -> tuple[int, int]: ...

class ComparisonOperator(Enum):
    Eq = ...
    Ne = ...
    Ge = ...
    Gt = ...
    Le = ...
    Lt = ...

class LogicalOperator(Enum):
    And = ...
    Or = ...

class FilterExpression:
    class True_:  # noqa: N801
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class False_:  # noqa: N801
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Null:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class StringLiteral:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Int:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> int: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Float:
        __match_args__ = ("value", "span")
        @property
        def value(self) -> float: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Not:
        __match_args__ = ("expression", "span")
        @property
        def expression(self) -> FilterExpression: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Logical:
        __match_args__ = ("left", "operator", "right", "span")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> LogicalOperator: ...
        @property
        def right(self) -> FilterExpression: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Comparison:
        __match_args__ = ("left", "operator", "right", "span")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> ComparisonOperator: ...
        @property
        def right(self) -> FilterExpression: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class RelativeQuery:
        __match_args__ = ("query", "span")
        @property
        def query(self) -> Query: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class RootQuery:
        __match_args__ = ("query", "span")
        @property
        def query(self) -> Query: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Function:
        __match_args__ = ("name", "args", "span")
        @property
        def name(self) -> str: ...
        @property
        def args(self) -> list[FilterExpression]: ...
        @property
        def span(self) -> tuple[int, int]: ...

class Selector:
    class Name:
        __match_args__ = ("name", "span")
        @property
        def name(self) -> str: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Index:
        __match_args__ = ("index", "span")
        @property
        def index(self) -> int: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Slice:
        __match_args__ = ("start", "stop", "step", "span")
        @property
        def start(self) -> int | None: ...
        @property
        def stop(self) -> int | None: ...
        @property
        def step(self) -> int | None: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Wild:
        __match_args__ = ("span",)
        @property
        def span(self) -> tuple[int, int]: ...

    class Filter:
        __match_args__ = ("expression", "span")
        @property
        def expression(self) -> FilterExpression: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class SingularQuery:
        __match_args__ = ("query", "span")
        @property
        def query(self) -> Query: ...
        @property
        def span(self) -> tuple[int, int]: ...

SelectorList = list[Selector]

class Segment:
    class Child:
        __match_args__ = ("selectors", "span")
        @property
        def selectors(self) -> SelectorList: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class Recursive:
        __match_args__ = ("selectors", "span")
        @property
        def selectors(self) -> SelectorList: ...
        @property
        def span(self) -> tuple[int, int]: ...

class Query:
    @property
    def segments(self) -> list[Segment]: ...
    def as_word(self) -> None | str: ...

def tokenize(source: str) -> list[Markup]: ...
def dump(source: str) -> None: ...
def dump_query(path: str) -> None: ...
def parse_query(path: str) -> Query: ...
def parse_jsonpath_query(path: str) -> Query: ...
def unescape_string(s: str) -> str: ...
def dummy_token() -> TokenT: ...

class PyLiquidError(Exception): ...
class LiquidTypeError(PyLiquidError): ...
class LiquidSyntaxError(PyLiquidError): ...
class LiquidNameError(PyLiquidError): ...
class LiquidExtensionError(PyLiquidError): ...

TokenT: TypeAlias = (
    Markup
    | Token
    | RangeArgument
    | Markup.Content
    | Markup.Raw
    | Markup.Comment
    | Markup.Output
    | Markup.Tag
    | Markup.Lines
    | Token.True_
    | Token.False_
    | Token.And
    | Token.Or
    | Token.In
    | Token.Not
    | Token.Contains
    | Token.Null
    | Token.If
    | Token.Else
    | Token.With
    | Token.Required
    | Token.As
    | Token.For
    | Token.Eq
    | Token.Ne
    | Token.Ge
    | Token.Gt
    | Token.Le
    | Token.Lt
    | Token.Colon
    | Token.Pipe
    | Token.DoublePipe
    | Token.Comma
    | Token.LeftParen
    | Token.RightParen
    | Token.Assign
    | Token.Word
    | Token.StringLiteral
    | Token.IntegerLiteral
    | Token.FloatLiteral
    | Token.RangeLiteral
    | Token.Query
    | RangeArgument.StringLiteral
    | RangeArgument.IntegerLiteral
    | RangeArgument.FloatLiteral
    | RangeArgument.Query
    | FilterExpression
    | FilterExpression.True_
    | FilterExpression.False_
    | FilterExpression.Null
    | FilterExpression.StringLiteral
    | FilterExpression.Int
    | FilterExpression.Not
    | FilterExpression.Logical
    | FilterExpression.Comparison
    | FilterExpression.RelativeQuery
    | FilterExpression.RootQuery
    | FilterExpression.Function
    | Selector
    | Selector.Name
    | Selector.Index
    | Selector.Slice
    | Selector.Wild
    | Selector.Filter
    | Selector.SingularQuery
    | Segment
    | Segment.Child
    | Segment.Recursive
)
