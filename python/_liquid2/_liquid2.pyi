from __future__ import annotations

from enum import Enum

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
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace, Whitespace, Whitespace]: ...
        @property
        def text(self) -> str: ...

    class Comment:
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def hashes(self) -> str: ...
        @property
        def text(self) -> str: ...

    class Output:
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def expression(self) -> list[ExpressionToken]: ...

    class Tag:
        @property
        def span(self) -> tuple[int, int]: ...
        @property
        def wc(self) -> tuple[Whitespace, Whitespace]: ...
        @property
        def name(self) -> str: ...
        @property
        def expression(self) -> list[ExpressionToken]: ...

    class EOI:
        pass

class ExpressionToken:
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

    class Word:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> str: ...

    class StringLiteral:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> str: ...

    class IntegerLiteral:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> int: ...

    class FloatLiteral:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> float: ...

    class RangeLiteral:
        @property
        def index(self) -> int: ...
        @property
        def start(self) -> RangeArgument: ...
        @property
        def stop(self) -> RangeArgument: ...

    class Query:
        @property
        def index(self) -> int: ...
        @property
        def path(self) -> Query: ...

class RangeArgument:
    class StringLiteral:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> str: ...

    class IntegerLiteral:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> int: ...

    class FloatLiteral:
        @property
        def index(self) -> int: ...
        @property
        def value(self) -> float: ...

    class Query:
        @property
        def index(self) -> int: ...
        @property
        def path(self) -> Query: ...

class ComparisonOp(Enum):
    Eq = ...
    Ne = ...
    Ge = ...
    Gt = ...
    Le = ...
    Lt = ...

class LogicalOp(Enum):
    And = ...
    Or = ...

class FilterExpression:
    class True_: ...  # noqa: N801
    class False_: ...  # noqa: N801
    class Null: ...

    class String:
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
        def operator(self) -> LogicalOp: ...
        @property
        def right(self) -> FilterExpression: ...

    class Comparison:
        __match_args__ = ("left", "operator", "right")
        @property
        def left(self) -> FilterExpression: ...
        @property
        def operator(self) -> ComparisonOp: ...
        @property
        def right(self) -> FilterExpression: ...

    class RelativeQuery:
        @property
        def query(self) -> Query: ...

    class RootQuery:
        @property
        def query(self) -> Query: ...

    class Function:
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

def tokenize(source: str) -> list[Markup]: ...
