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
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def text(self) -> str: ...

    class Raw:
        __match_args__ = ("span", "wc", "text")
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace, Whitespace, Whitespace]: ...
        @property
        def text(self) -> str: ...

    class Comment:
        __match_args__ = ("span", "wc", "hashes", "text")
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def hashes(self) -> str: ...
        @property
        def text(self) -> str: ...

    class Output:
        __match_args__ = ("span", "wc", "expression")
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def expression(self) -> list[Token]: ...

    class Tag:
        __match_args__ = ("span", "wc", "name", "expression")
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def name(self) -> str: ...
        @property
        def expression(self) -> list[Token]: ...

    class EOI:
        pass

class Token:
    class True_:  # noqa: N801
        @property
        def index(self) -> int: ...

    class False_:  # noqa: N801
        @property
        def index(self) -> int: ...

    class And:
        @property
        def index(self) -> int: ...

    class Or:
        @property
        def index(self) -> int: ...

    class In:
        @property
        def index(self) -> int: ...

    class Not:
        @property
        def index(self) -> int: ...

    class Contains:
        @property
        def index(self) -> int: ...

    class Null:
        @property
        def index(self) -> int: ...

    class If:
        @property
        def index(self) -> int: ...

    class Else:
        @property
        def index(self) -> int: ...

    class With:
        @property
        def index(self) -> int: ...

    class As:
        @property
        def index(self) -> int: ...

    class For:
        @property
        def index(self) -> int: ...

    class Eq:
        @property
        def index(self) -> int: ...

    class Ne:
        @property
        def index(self) -> int: ...

    class Ge:
        @property
        def index(self) -> int: ...

    class Gt:
        @property
        def index(self) -> int: ...

    class Le:
        @property
        def index(self) -> int: ...

    class Lt:
        @property
        def index(self) -> int: ...

    class Colon:
        @property
        def index(self) -> int: ...

    class Pipe:
        @property
        def index(self) -> int: ...

    class DoublePipe:
        @property
        def index(self) -> int: ...

    class Comma:
        @property
        def index(self) -> int: ...

    class LeftParen:
        @property
        def index(self) -> int: ...

    class RightParen:
        @property
        def index(self) -> int: ...

    class Assign:
        @property
        def index(self) -> int: ...

    class Word:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> str: ...

    class StringLiteral:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> str: ...

    class IntegerLiteral:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> int: ...

    class FloatLiteral:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> float: ...

    class RangeLiteral:
        __match_args__ = ("index", "start", "stop")
        @property
        def index(self) -> int: ...
        @property
        def start(self) -> RangeArgument: ...
        @property
        def stop(self) -> RangeArgument: ...

    class Query:
        __match_args__ = ("index", "path")
        @property
        def index(self) -> int: ...
        @property
        def path(self) -> Query: ...

class RangeArgument:
    class StringLiteral:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> str: ...

    class IntegerLiteral:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> int: ...

    class FloatLiteral:
        __match_args__ = ("index", "value")
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> float: ...

    class Query:
        __match_args__ = ("index", "path")
        @property
        def index(self) -> int: ...
        @property
        def path(self) -> Query: ...

TokenT: TypeAlias = (
    Markup
    | Token
    | RangeArgument
    | Markup.Content
    | Markup.Raw
    | Markup.Comment
    | Markup.Output
    | Markup.Tag
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
    class True_: ...  # noqa: N801
    class False_: ...  # noqa: N801
    class Null: ...

    class StringLiteral:
        __match_args__ = ("value",)
        @property
        def value(self) -> str: ...

    class Int:
        __match_args__ = ("value",)
        @property
        def value(self) -> int: ...

    class Float:
        __match_args__ = ("value",)
        @property
        def value(self) -> float: ...

    class Not:
        __match_args__ = ("expression",)
        @property
        def expression(self) -> FilterExpression: ...

    class Logical:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> LogicalOperator: ...
        @property
        def right(self) -> FilterExpression: ...

    class Comparison:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> ComparisonOperator: ...
        @property
        def right(self) -> FilterExpression: ...

    class RelativeQuery:
        __match_args__ = ("query",)
        @property
        def query(self) -> Query: ...

    class RootQuery:
        __match_args__ = ("query",)
        @property
        def query(self) -> Query: ...

    class Function:
        __match_args__ = ("name", "args")
        @property
        def name(self) -> str: ...
        @property
        def args(self) -> list[FilterExpression]: ...

class Selector:
    class Name:
        __match_args__ = ("name",)
        @property
        def name(self) -> str: ...

    class Index:
        __match_args__ = ("index",)
        @property
        def index(self) -> int: ...

    class Slice:
        __match_args__ = ("start", "stop", "step")
        @property
        def start(self) -> int | None: ...
        @property
        def stop(self) -> int | None: ...
        @property
        def step(self) -> int | None: ...

    class Wild: ...

    class Filter:
        __match_args__ = ("expression",)
        @property
        def expression(self) -> FilterExpression: ...

    class SingularQuery:
        __match_args__ = ("query",)
        @property
        def query(self) -> Query: ...

SelectorList = list[Selector]

class Segment:
    class Child:
        __match_args__ = ("selectors", "span")
        @property
        def selectors(self) -> SelectorList: ...

    class Recursive:
        __match_args__ = ("selectors", "span")
        @property
        def selectors(self) -> SelectorList: ...

class Query:
    @property
    def segments(self) -> list[Segment]: ...
    def as_word(self) -> None | str: ...

def tokenize(source: str) -> list[Markup]: ...
def dump(source: str) -> None: ...
def parse_query(path: str) -> Query: ...

class PyLiquidError(Exception): ...
class LiquidTypeError(PyLiquidError): ...
class LiquidSyntaxError(PyLiquidError): ...
class LiquidNameError(PyLiquidError): ...
class LiquidExtensionError(PyLiquidError): ...
