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
        __match_args__ = ("wc", "statements", "span")
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def statements(self) -> list[list[Token]]: ...
        @property
        def span(self) -> tuple[int, int]: ...

    class EOI:
        pass

class Token:
    class True_:  # noqa: N801
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class False_:  # noqa: N801
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class And:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Or:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class In:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Not:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Contains:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Null:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class If:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Else:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class With:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class As:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class For:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Eq:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Ne:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Ge:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Gt:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Le:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Lt:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Colon:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Pipe:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class DoublePipe:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Comma:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class LeftParen:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class RightParen:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Assign:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Word:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> str: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class StringLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> str: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class IntegerLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> int: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class FloatLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> float: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class RangeLiteral:
        __match_args__ = ("start", "stop", "line_col")
        @property
        def start(self) -> RangeArgument: ...
        @property
        def stop(self) -> RangeArgument: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Query:
        __match_args__ = ("path", "line_col")
        @property
        def path(self) -> Query: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

class RangeArgument:
    class StringLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> str: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class IntegerLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> int: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class FloatLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> float: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Query:
        __match_args__ = ("path", "line_col")
        @property
        def path(self) -> Query: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

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
)

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
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class False_:  # noqa: N801
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Null:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class StringLiteral:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> str: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Int:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> int: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Float:
        __match_args__ = ("value", "line_col")
        @property
        def value(self) -> float: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Not:
        __match_args__ = ("expression", "line_col")
        @property
        def expression(self) -> FilterExpression: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Logical:
        __match_args__ = ("left", "operator", "right", "line_col")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> LogicalOperator: ...
        @property
        def right(self) -> FilterExpression: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Comparison:
        __match_args__ = ("left", "operator", "right", "line_col")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> ComparisonOperator: ...
        @property
        def right(self) -> FilterExpression: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class RelativeQuery:
        __match_args__ = ("query", "line_col")
        @property
        def query(self) -> Query: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class RootQuery:
        __match_args__ = ("query", "line_col")
        @property
        def query(self) -> Query: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Function:
        __match_args__ = ("name", "args", "line_col")
        @property
        def name(self) -> str: ...
        @property
        def args(self) -> list[FilterExpression]: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

class Selector:
    class Name:
        __match_args__ = ("name", "line_col")
        @property
        def name(self) -> str: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Index:
        __match_args__ = ("index", "line_col")
        @property
        def index(self) -> int: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Slice:
        __match_args__ = ("start", "stop", "step", "line_col")
        @property
        def start(self) -> int | None: ...
        @property
        def stop(self) -> int | None: ...
        @property
        def step(self) -> int | None: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Wild:
        __match_args__ = ("line_col",)
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Filter:
        __match_args__ = ("expression", "line_col")
        @property
        def expression(self) -> FilterExpression: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class SingularQuery:
        __match_args__ = ("query", "line_col")
        @property
        def query(self) -> Query: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

SelectorList = list[Selector]

class Segment:
    class Child:
        __match_args__ = ("selectors", "line_col")
        @property
        def selectors(self) -> SelectorList: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

    class Recursive:
        __match_args__ = ("selectors", "line_col")
        @property
        def selectors(self) -> SelectorList: ...
        @property
        def line_col(self) -> tuple[int, int]: ...

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

class PyLiquidError(Exception): ...
class LiquidTypeError(PyLiquidError): ...
class LiquidSyntaxError(PyLiquidError): ...
class LiquidNameError(PyLiquidError): ...
class LiquidExtensionError(PyLiquidError): ...
